#!/usr/bin/env python3
import uuid
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import sys

def generate_uuid():
    """Generate a UUID string without dashes."""
    return "i" + str(uuid.uuid4()).replace("-", "")

def create_xml_element(parent, tag, text=None):
    """Create an XML element with optional text content."""
    element = ET.SubElement(parent, tag)
    if text is not None:
        element.text = text
    return element

def create_question_item(section, question_num, question_text, options, correct_answer_index, points=5):
    """Create a question item in the XML structure."""
    # Generate unique identifiers
    item_id = generate_uuid()
    assessment_id = generate_uuid()
    
    # Create the item element
    item = ET.SubElement(section, "item", {"ident": item_id, "title": f"Question {question_num}"})
    
    # Create itemmetadata
    itemmetadata = create_xml_element(item, "itemmetadata")
    qtimetadata = create_xml_element(itemmetadata, "qtimetadata")
    
    # Add metadata fields
    field1 = create_xml_element(qtimetadata, "qtimetadatafield")
    create_xml_element(field1, "fieldlabel", "question_type")
    create_xml_element(field1, "fieldentry", "multiple_choice_question")
    
    field2 = create_xml_element(qtimetadata, "qtimetadatafield")
    create_xml_element(field2, "fieldlabel", "points_possible")
    create_xml_element(field2, "fieldentry", str(points))
    
    field3 = create_xml_element(qtimetadata, "qtimetadatafield")
    create_xml_element(field3, "fieldlabel", "assessment_question_identifierref")
    create_xml_element(field3, "fieldentry", assessment_id)
    
    # Create presentation
    presentation = create_xml_element(item, "presentation")
    material = create_xml_element(presentation, "material")
    create_xml_element(material, "mattext", question_text).set("texttype", "text/html")
    
    # Create response lid
    response_lid = ET.SubElement(presentation, "response_lid", {"ident": "response1", "rcardinality": "Single"})
    render_choice = create_xml_element(response_lid, "render_choice")
    
    # Add options
    for i, option_text in enumerate(options):
        option_id = f"{question_num}00{i}"
        response_label = ET.SubElement(render_choice, "response_label", {"ident": option_id})
        option_material = create_xml_element(response_label, "material")
        create_xml_element(option_material, "mattext", option_text).set("texttype", "text/plain")
    
    # Create response processing
    resprocessing = create_xml_element(item, "resprocessing")
    outcomes = create_xml_element(resprocessing, "outcomes")
    ET.SubElement(outcomes, "decvar", {"maxvalue": "100", "minvalue": "0", "varname": "SCORE", "vartype": "Decimal"})
    
    # Set correct answer
    respcondition = ET.SubElement(resprocessing, "respcondition", {"continue": "No"})
    conditionvar = create_xml_element(respcondition, "conditionvar")
    
    # Calculate the correct answer option ID (e.g., 1001, 2002, etc.)
    correct_option_id = f"{question_num}00{int(correct_answer_index)-1}"
    
    create_xml_element(conditionvar, "varequal", correct_option_id).set("respident", "response1")
    ET.SubElement(respcondition, "setvar", {"action": "Set", "varname": "SCORE"}).text = "100"
    
    return item

def create_canvas_xml(quiz_title, questions, max_attempts=1):
    """Create the full Canvas-compatible XML structure."""
    # Create root element with namespace
    root = ET.Element("questestinterop", {
        "xmlns": "http://www.imsglobal.org/xsd/ims_qtiasiv1p2",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "http://www.imsglobal.org/xsd/ims_qtiasiv1p2 http://www.imsglobal.org/xsd/ims_qtiasiv1p2p1.xsd"
    })
    
    # Create assessment element
    assessment_id = "ifc" + str(uuid.uuid4()).replace("-", "")[:28]
    assessment = ET.SubElement(root, "assessment", {"ident": assessment_id, "title": quiz_title})
    
    # Add metadata for max attempts
    qtimetadata = create_xml_element(create_xml_element(assessment, "qtimetadata"), "qtimetadatafield")
    create_xml_element(qtimetadata, "fieldlabel", "cc_maxattempts")
    create_xml_element(qtimetadata, "fieldentry", str(max_attempts))
    
    # Create section
    section = ET.SubElement(assessment, "section", {"ident": "root_section"})
    
    # Add questions
    for i, question_data in enumerate(questions, 1):
        create_question_item(
            section,
            i,
            question_data["question"],
            question_data["options"],
            question_data["correct_answer_index"],
            question_data["points"]
        )
    
    # Format the XML properly with indentation
    rough_string = ET.tostring(root, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def parse_tab_delimited(file_path):
    """Parse tab-delimited text file with exactly the format provided in paste.txt."""
    questions = []
    
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            # Skip blank lines
            if not line.strip():
                continue
                
            # Split by tabs
            parts = line.strip().split('\t')
            
            # If we don't get enough parts, skip
            if len(parts) < 9:
                continue
                
            # Only process multiple choice questions
            if parts[0] != "MC":
                continue
                
            # Extract data based on the exact format in paste.txt
            question_type = parts[0]  # MC
            # parts[1] is empty
            points = int(parts[2])    # 5
            question_text = parts[3]  # Question text
            correct_answer_index = parts[4]  # Index of correct answer (1-4)
            options = parts[5:9]      # The 4 answer options
            
            questions.append({
                "question": question_text,
                "options": options,
                "correct_answer_index": correct_answer_index,
                "points": points
            })
    
    return questions

def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python simple-converter.py input_file [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "GPS_Quiz.xml"
    
    # Parse the input file
    try:
        questions = parse_tab_delimited(input_file)
        if not questions:
            print("No valid questions found in the input file.")
            sys.exit(1)
        
        # Generate the XML
        xml_content = create_canvas_xml("Genealogical Proof Standard Quiz", questions)
        
        # Write to file
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(xml_content)
            
        print(f"Successfully converted {len(questions)} questions to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
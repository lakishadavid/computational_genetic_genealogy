#!/usr/bin/env python3
import uuid
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import sys
import csv
import os
import zipfile
import time

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
        if option_text:  # Skip empty options
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

def parse_csv_file(file_path):
    """Parse a CSV file with a flexible format."""
    questions = []
    
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if not row or len(row) < 5:  # Skip empty or too short rows
                continue
                
            # Expected format: question_type, blank, points, question_text, correct_answer_index, option1, option2, ... optionN
            question_type = row[0]
            
            # Only process multiple choice questions for now
            if question_type != "MC":
                continue
                
            # Extract data
            try:
                points = int(row[2])
                question_text = row[3]
                correct_answer_index = row[4].strip()
                
                # Make sure correct_answer_index is numeric
                if not correct_answer_index.isdigit():
                    print(f"Warning: Invalid correct answer index: '{correct_answer_index}' in row: {row}")
                    continue
                
                # Collect all non-empty options
                options = [opt.strip() for opt in row[5:] if opt.strip()]
                
                if options and correct_answer_index:
                    questions.append({
                        "question": question_text,
                        "options": options,
                        "correct_answer_index": correct_answer_index,
                        "points": points
                    })
            except (IndexError, ValueError) as e:
                print(f"Warning: Skipping malformed row: {row}. Error: {e}")
    
    return questions

def create_zip_file(xml_file_path, zip_file_path=None):
    """Create a zip file containing the XML file."""
    if zip_file_path is None:
        # Use the same name but with .zip extension
        zip_file_path = os.path.splitext(xml_file_path)[0] + ".zip"
    
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        zipf.write(xml_file_path, os.path.basename(xml_file_path))
    
    return zip_file_path

def process_quiz_file(input_file, quiz_title=None, output_dir=None, max_attempts=1):
    """Process a quiz file and create Canvas-compatible files."""
    # Generate base names
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    if quiz_title is None:
        quiz_title = base_name.replace("_", " ")
    
    # Add timestamp to avoid overwrites
    timestamp = int(time.time())
    
    # Set output directory
    if output_dir is None:
        output_dir = os.path.dirname(input_file)
    
    # Generate output paths
    xml_file_path = os.path.join(output_dir, f"{base_name}_{timestamp}.xml")
    zip_file_path = os.path.join(output_dir, f"{base_name}_{timestamp}.zip")
    
    # Parse the input file
    questions = parse_csv_file(input_file)
    if not questions:
        print(f"No valid questions found in {input_file}.")
        return None
    
    # Generate the XML
    xml_content = create_canvas_xml(quiz_title, questions, max_attempts)
    
    # Write XML file
    with open(xml_file_path, "w", encoding="utf-8") as file:
        file.write(xml_content)
    
    # Create zip file
    create_zip_file(xml_file_path, zip_file_path)
    
    # Clean up the temporary XML file
    os.remove(xml_file_path)
    
    return zip_file_path

def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python improved-quiz-converter.py input_file [quiz_title] [output_dir] [max_attempts]")
        print("Example: python improved-quiz-converter.py quizzes/my_quiz.csv 'My Quiz Title' quizzes 2")
        sys.exit(1)
    
    input_file = sys.argv[1]
    quiz_title = sys.argv[2] if len(sys.argv) > 2 else None
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    max_attempts = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    
    try:
        zip_file = process_quiz_file(input_file, quiz_title, output_dir, max_attempts)
        if zip_file:
            print(f"Successfully created {zip_file}")
        else:
            print("Failed to create quiz file.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
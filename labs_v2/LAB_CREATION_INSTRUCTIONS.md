# Lab Creation Instructions for Computational Genetic Genealogy

## Purpose

I need assistance creating comprehensive laboratory notebooks for the "Computational Pedigree Reconstruction: Deep Dive into Bonsai v3" course. These labs should provide hands-on experience with the actual Bonsai v3 codebase.

## Resources

- Bonsai v3 codebase: `/home/lakishadavid/computational_genetic_genealogy/utils/bonsaitree`
- Course plan: `/home/lakishadavid/computational_genetic_genealogy/docs/slides/course_plan_cgg.md`
- Template: `Lab00_Template.ipynb`
- Existing labs: Labs 1-22 are already complete

## Requirements

1. Create one lab for each remaining session (23-30) listed in the course plan
2. Each lab must strictly follow the session topic outlined in the course plan
3. Use the **actual Bonsai v3 functions** as much as possible rather than simplified versions
4. Follow the structure and formatting of `Lab00_Template.ipynb`
5. Include detailed explanations, exercises, and examples showing real-world applications
6. Provide clear instructions and expected outcomes for each exercise
7. Incorporate appropriate visualizations where relevant
8. Include challenge problems or extensions for advanced students
9. Add references to relevant academic papers or resources

## Lab Structure

Each lab should follow this structure:

1. **Overview** - Introduction to the lab topic and objectives
2. **Standard imports and setup** - Python imports and environment configuration
3. **Bonsai module paths** - Code to access the Bonsai v3 codebase
4. **Helper functions** - Functions to explore modules, display source code, etc.
5. **Bonsai installation check** - Verification that Bonsai modules are accessible
6. **Content sections** (typically 3 parts):
   - Part 1: Introduces fundamental concepts
   - Part 2: Explores implementation details
   - Part 3: Applies concepts to practical examples
7. **Summary** - Key takeaways from the lab
8. **PDF conversion code** - Code to convert notebook to PDF format (at the end)

## Implementation Guidelines

1. **Code Access Approach**:

   - Use `view_source()` to show students the actual implementation of key functions
   - Reference and explain the original source code rather than creating simplified versions
   - Use the **actual Bonsai v3 functions** as much as possible rather than simplified versions
   - When simplifications are necessary, clearly indicate why and how they differ from the original

2. **JupyterLite Compatibility**:

   - Provide conditional implementations only when absolutely necessary for JupyterLite compatibility
   - Use conditional imports: `if is_jupyterlite(): # Simplified implementation else: # Use actual Bonsai`

3. **Visualization**:

   - Create visualizations of pedigrees, relationships, and data structures
   - Use networkx for pedigree visualization when appropriate

4. **Practical Examples**:
   - Include real-world examples where possible
   - Show how concepts apply to genetic genealogy problems

## Deliverables

- Complete Jupyter notebook files for each lab following the naming convention Lab[XX]\_[Topic].ipynb
- Include answer keys or solution guides as separate files where appropriate

Please examine the existing labs (1-9) to maintain consistency in style, difficulty progression, and pedagogical approach.

Sometimes the labs will be too large to complete all at one time. You will need to first create a smaller partial lab. Then revise it by adding more of the content. You should continue doing this until you have saved the complete lab. In this way, the lab length does not have to be limited to what you can handle in one save.

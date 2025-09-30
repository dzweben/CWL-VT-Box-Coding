# Qualitative Thematic Analysis Coding Project

## Overview  
This repository supports my **qualitative thematic analysis** projects. It houses scripts that automate the generation and visualization of **themes, subthemes, and verbatim participant quotes** from focus group data. The goal is to move from raw transcripts → structured APA-style tables → interactive atlases that make qualitative data easier to explore, share, and publish.  

The broader project involves analyzing school counselors’ experiences with the *School Counselor Care and Support Box*. The analysis identifies both **deductive themes** (derived from research questions) and **inductive themes** (emerging from participants’ narratives).  

## What I’m Working On  
- Conducting thematic analysis of focus group data.  
- Organizing results into structured **theme jawn** (deductive + inductive themes, subthemes, supporting quotes).  
- Building scripts that automatically generate **APA-compliant Word tables** and **interactive atlases**.  
- Ensuring reproducibility and consistency across multiple qualitative projects.  

---

## Script: `dedthemes_table_gen.py`  
This script generates a **Word document** with a clean APA-style table of **deductive themes, subthemes, and participant quotes**.  

**Key Features:**  
1. Creates a new Word document.  
2. Adds a centered, italicized APA-style title above the table.  
3. Generates a three-column table with **Deductive Theme, Subtheme, and Quotes**.  
4. Populates each row with verbatim participant quotes (no editing or trimming).  
5. Applies borders for readability (qualitative tables are dense).  
6. Adds a table note clarifying participant labels (e.g., P1, P2).  
7. Saves the output as `Deductive_Themes_APA.docx`.  

**Usage:**  
    python dedthemes_table_gen.py  

Output: `Deductive_Themes_APA.docx`

---

## Script: `indthemes_table_gen.py`  
This script generates a **Word document** with a clean APA-style table of **inductive themes, subthemes, and participant quotes**.  

**Key Features:**  
1. Creates a new Word document in **Times New Roman** (APA standard).  
2. Adds a centered, italicized APA-style title above the table.  
3. Generates a three-column table with **Inductive Theme, Subtheme, and Quotes**.  
4. Preserves **line breaks** after each quote for readability.  
5. Populates each row with verbatim participant quotes (no trimming, full fidelity).  
6. Saves the output as `Inductive_Themes_APA.docx`.  

**Usage:**  
    python indthemes_table_gen.py  

Output: `Inductive_Themes_APA.docx`

---

## Script: `theme_quote_atlas.builder.py`  
This script transforms a coded PDF of themes and quotes into a fully **interactive Quote Atlas**.  

**Key Features:**  
1. Parses **Themes → Subthemes → Quotes** hierarchy from a PDF.  
2. Exports an **interactive HTML atlas** with:  
   - Collapsible sections for each theme/subtheme.  
   - A **live search bar** (filter by keywords or participant #).  
   - A sticky **table of contents** for easy navigation.  
   - One-click **copy buttons** on each quote.  
3. Exports a parallel **JSON file** of all data (for further analysis or integration).  
4. Designed to work offline — open the `.html` in any browser and it runs without a server.  

**Usage:**  
    python theme_quote_atlas.builder.py  

**Outputs:**  
- `quote_atlas.html` → Interactive atlas (open in browser).  
- `quotes.json` → Clean JSON dump of themes, subthemes, and quotes.  

**Why it’s cool:**  
- Makes dense qualitative data actually explorable.  
- Lets researchers search across participants and themes instantly.  
- Copy/paste quotes directly for papers, reports, or presentations.  
- JSON export enables mixing qualitative themes with quant data downstream.  

---

## Script: `stage1_atlasbuilder.py`  
This script processes the **Stage 1 coding sheets**, linking **raw transcripts** to the **first-round coding notes**. It produces an interactive atlas where annotations are directly connected to the quotes they interpret.  

**Key Features:**  
1. Parses DOCX transcripts and coding notes.  
2. Distinguishes between **raw transcript lines** (speaker + timestamp) and **Stage 1 annotations** (bulleted coding comments).  
3. Attaches each annotation to the **exact prior transcript quote** it refers to.  
4. Exports an **interactive HTML atlas** with toggle views:  
   - **Raw Transcript** (all speaker lines by time).  
   - **Stage 1 Coding** (annotations with direct links to referenced quotes).  
5. Provides **live search** across transcript and coding notes.  
6. Exports a clean **JSON structure** with transcript lines + annotations for reuse.  

**Usage:**  
    python stage1_atlasbuilder.py  

**Outputs:**  
- `stage1_atlas.html` → Interactive atlas with raw + coding views.  
- `stage1_data.json` → Structured JSON of transcript and annotations.  

**Why it’s cool:**  
- Bridges transcripts and first-stage coding in one interface.  
- Allows instant navigation from notes → supporting quotes.  
- Makes collaborative qualitative coding transparent and shareable.  


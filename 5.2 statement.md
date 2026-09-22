# Problem Statement

Many teams need a simple and consistent way to identify, evaluate, and communicate operational risks. Risk information is often recorded in unstructured notes or separate spreadsheets, making it difficult to compare risks, determine which risks require immediate attention, and prepare clear reports. Manual scoring can also lead to inconsistent results and make it harder to maintain a shared view of current risks.

The Risk Analyzer System addresses this problem by providing a local command-line application that stores risk information in structured JSON or CSV files, calculates risk scores from likelihood and impact, assigns priority levels, sorts risks by urgency, and produces readable reports. The system uses only Python's standard library so that it can be run without external services or third-party dependencies.

# Scope of the Project

The project covers the analysis and reporting of operational risks maintained in local files. Its scope includes:

- Defining and validating structured risk records.
- Accepting risk data in JSON and CSV formats.
- Allowing users to add a risk interactively from the command line.
- Calculating a risk score by multiplying likelihood by impact.
- Classifying risks as Low, Medium, High, or Critical according to configurable thresholds.
- Sorting risks from the highest score to the lowest score.
- Displaying summaries and detailed results in the terminal.
- Exporting reports as text, JSON, or CSV files.
- Providing sample data and automated tests for the main application behavior.

The project does not include authentication, multi-user access, a hosted database, a graphical user interface, cloud deployment, real-time integrations, or automated changes to external systems. It is intended to be a local file-based analysis tool and demonstration project.

# Target Users

The target users are:

- Operations teams that need to maintain and prioritize operational risks.
- Project managers who need a consistent method for reviewing project risks.
- Risk and compliance teams preparing risk summaries and reports.
- Small organizations that need a lightweight risk assessment tool without infrastructure costs.
- Students and developers learning about modular Python applications, command-line interfaces, data validation, and automated testing.

# High-Level Features

The Risk Analyzer System provides the following high-level features:

1. **Structured risk management** — Records include an identifier, title, description, category, likelihood, impact, owner, status, and mitigation plan.
2. **Input validation** — Required fields are checked, and likelihood and impact values are restricted to the accepted range of 1 through 5.
3. **Risk scoring** — Each risk receives a numerical score based on likelihood multiplied by impact.
4. **Priority classification** — Scores are mapped to Low, Medium, High, or Critical priority levels.
5. **Risk prioritization** — Risks are ordered from most urgent to least urgent based on their scores.
6. **Multiple file formats** — Risk data can be loaded from JSON or CSV files.
7. **Interactive risk entry** — Users can add a risk through prompts in the command line.
8. **Report generation** — Results can be viewed in the terminal or exported as text, JSON, or CSV reports.
9. **Configurable thresholds** — Priority bands can be adjusted through the project configuration file.
10. **Portable implementation** — The application runs on Windows, macOS, and Linux using Python's standard library only.
11. **Automated testing** — Built-in tests verify scoring, validation, loading, ordering, and report generation behavior.

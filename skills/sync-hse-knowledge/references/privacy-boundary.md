# Privacy & Health Data Boundary Specification

## 1. Strict Privacy & Health Record Separation

The HSE Knowledge Base strictly excludes individual health and personally identifiable information (PII):

- **No Medical Records**: Diagnosis, medical imaging, clinical test results, or worker-identifiable physical examination records must NEVER enter the general knowledge store or vector embeddings.
- **Similar Exposure Groups (SEG)**: Exposure data is managed strictly at the aggregate or role/activity level (e.g. "Welder Group A - Fabrication Shop").
- **Fitness-to-Work Boundary**: External occupational health systems may only transmit aggregate fitness status (`fit`, `fit_with_restrictions`, `temporarily_unfit`) without diagnostic details.
- **Redaction**: Incoming documents are sanitized to strip employee national ID numbers, personal phone numbers, and home addresses before storage.

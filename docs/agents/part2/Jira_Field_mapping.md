# KNOWLEDGE BASE: JIRA SERVICE MANAGEMENT FIELD MAPPING PROTOCOL

## 1. PURPOSE
This document defines the specific logic for populating Jira Service Management (JSM) fields via the REST API. Use this as the "Source of Truth" when generating Python code for ticket creation.

## 2. TARGET ENDPOINT
- **Endpoint:** `POST /rest/servicedeskapi/request`
- **Logic:** This endpoint is mandatory because it handles "on-the-fly" customer creation for external email addresses.
- **Header Requirement:** `{"X-ExperimentalApi": "opt-in"}` must be included.

## 3. CORE FIELD POPULATION (MANDATORY)
| Jira Parameter | Source Data | Format |
| :--- | :--- | :--- |
| `raiseOnBehalfOf` | Parsed Sender Email | String (e.g., "user@example.com") |
| `serviceDeskId` | Project ID | String (Numeric) |
| `requestTypeId` | Specific Portal Form ID | String (Numeric) |

## 4. CUSTOM FIELD MAPPING (requestFieldValues)
All payload data must be nested inside the `requestFieldValues` object. Do NOT use the `fields` top-level key.

### A. Mapping Schema
| Payload Key | Jira Custom Field ID | Logic/Requirement |
| :--- | :--- | :--- |
| `subject` | `summary` | Standard string. |
| `body` | `description` | Standard string. |
| `dept_name` | `customfield_10101` | Must match Jira "Select List" options exactly. |
| `external_ref` | `customfield_10102` | Short text/ID. |
| `payload_json` | `customfield_10103` | Multi-line text for raw audit data. |

### B. Transformation Rules
- **Null Handling:** If a payload key is missing, do NOT include the `customfield_XXXX` key in the dictionary.
- **Date Handling:** Convert any timestamps to ISO-8601 `YYYY-MM-DD` format.
- **String Cleaning:** Strip leading/trailing whitespaces from email addresses before assigning to `raiseOnBehalfOf`.

## 5. PYTHON IMPLEMENTATION SNIPPET ( optional suggestion)
When amending code, use this dictionary construction pattern:

```python
def generate_jsm_payload(parsed_email_data):
    # Construct the internal field map
    field_values = {
        "summary": parsed_email_data.get("subject"),
        "description": parsed_email_data.get("body"),
        "customfield_10101": parsed_email_data.get("department"),
        "customfield_10102": parsed_email_data.get("external_id")
    }
    
    # Filter out None values to prevent API validation errors
    clean_fields = {k: v for k, v in field_values.items() if v is not None}
    
    return {
        "serviceDeskId": "1",
        "requestTypeId": "10",
        "raiseOnBehalfOf": parsed_email_data.get("sender_email"),
        "requestFieldValues": clean_fields
    }


6. CRITICAL CONSTRAINTS
No User Lookup: Do not use accountId. Use the raw email in raiseOnBehalfOf.

Visibility: Custom fields MUST be added to the JSM "Request Type" view configuration in the Jira UI, or the API will reject the request.

Auth: Use Basic Auth with an API Token, not a personal password.


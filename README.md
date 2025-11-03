# ISO 8583 Message Generator for Faster Payment System (FPS)

Python scripts for generating ISO 8583 messages and bitmaps for Faster Payment System (FPS) messages.

## Overview

This repository contains two tools:

1. **bitmap_generator.py** - Generates bitmap files from JSON field metadata (indicates which fields are present)
2. **iso8583_message_generator.py** - Generates complete ISO 8583 messages with formatted field data

### ISO 8583 Message Structure

The complete message format follows the ISO 8583 standard:

- **First 4 characters**: Message ID (e.g., "0200")
- **Next 16 bytes (32 hex chars)**: Primary bitmap indicating presence of fields 1-64
- **Next 16 bytes (32 hex chars)**: Secondary bitmap indicating presence of fields 65-128
- **Remaining data**: Formatted field values in order

The bitmap uses bit positions to indicate which fields are present in a message. Bit 0 (leftmost) of the primary bitmap is set to 1 if the secondary bitmap is present.

## Requirements

- Python 3.6 or higher
- No external dependencies required (uses only standard library)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/padmamanasaP/bitmapCreation.git
cd bitmapCreation
```

2. Make the script executable (optional):
```bash
chmod +x bitmap_generator.py
```

## Usage

### Tool 1: Bitmap Generator (bitmap_generator.py)

Generates bitmap files indicating which fields are present (no field data).

#### Basic Usage

Generate a bitmap from all fields in a JSON file:

```bash
python3 bitmap_generator.py -i dataElementsMeta.json -o bitmap.txt
```

### Tool 2: ISO 8583 Message Generator (iso8583_message_generator.py)

Generates complete ISO 8583 messages with formatted field data.

#### Basic Usage

Generate a complete ISO 8583 message:

```bash
python3 iso8583_message_generator.py -m dataElementsMeta.json -d field_data.json -o message.txt
```

### Command Line Options

#### Bitmap Generator Options

```
-i, --input INPUT        Input JSON file with field metadata (required)
-o, --output OUTPUT      Output bitmap file path (required)
-m, --message-id ID      4-character message ID (default: 0200)
-f, --fields FIELDS      Comma-separated list of field numbers to include
-v, --verbose            Print detailed bitmap information
```

#### ISO 8583 Message Generator Options

```
-m, --metadata FILE      Field metadata JSON file (dataElementsMeta.json) (required)
-d, --data FILE          Field data JSON file with actual values (required)
-o, --output FILE        Output message file path (required)
--message-id ID          4-character message ID (default: 0200)
-v, --verbose            Print detailed message information
```

### Examples

#### Example 1: Generate bitmap with all fields

```bash
python3 bitmap_generator.py -i dataElementsMeta.json -o bitmap.txt
```

Output:
```
✓ Bitmap file generated successfully: bitmap.txt
  Content: 0200BE72016B21FFA0CC3B000FA279EE1FFF
  Length: 36 characters
```

#### Example 2: Generate bitmap with custom message ID

```bash
python3 bitmap_generator.py -i dataElementsMeta.json -o bitmap.txt -m 0210
```

This generates a bitmap with message ID "0210" instead of the default "0200".

#### Example 3: Generate bitmap for specific fields only

```bash
python3 bitmap_generator.py -i sample_fields.json -o bitmap.txt -f 3,4,6,7,11,12
```

This generates a bitmap containing only fields 3, 4, 6, 7, 11, and 12.

#### Example 4: Verbose output with detailed information

```bash
python3 bitmap_generator.py -i sample_fields.json -o bitmap.txt -v
```

Output:
```
✓ Bitmap file generated successfully: bitmap.txt
  Content: 0200B6300002206000000000000240000000
  Length: 36 characters

Detailed Bitmap Information:
============================================================
Message ID: 0200

Primary Bitmap (Fields 1-64):
  Binary: 1011011000110000000000000000001000100000011000000000000000000000
  Hex: B630000220600000
  Present fields: [1, 3, 4, 6, 7, 11, 12, 31, 35, 42, 43]

Secondary Bitmap (Fields 65-128):
  Binary: 0000000000000000000000000000001001000000000000000000000000000000
  Hex: 0000000240000000
  Present fields: [95, 98]
```

## ISO 8583 Message Generator - Field Formatting Rules

The ISO 8583 message generator applies the following formatting rules based on field metadata:

### 1. Date Fields (data_type: "date")
- **Input format**: "YYYY-MM-DD HH:MM:SS"
- **Output format**: Extracted from `value_constraints` field in metadata
- **Examples**:
  - Field 7: "2024-11-03 14:30:45" → "1103143045" (MMDDhhmmss)
  - Field 12: "2024-11-03 00:00:00" → "20241103" (YYYYMMDD)

### 2. Numeric Fixed-Length Fields (data_type: "numeric", length_type: "fixed")
- **Formatting**: Zero-padded to specified length
- **Examples**:
  - Field 6 (length 14): "50000" → "00000000050000"
  - Field 11 (length 6): "123456" → "123456"

### 3. Subfields
- **Handling**: Values provided as dictionary with subfield tags
- **Formatting**: Same rules apply recursively to each subfield
- **Example**:
  ```json
  "f3": {
    "pymt_type_code": "01",
    "sender_code": "02",
    "receiver_code": "03"
  }
  ```
  Output: "010203"

### 4. Variable Alphanumeric Fields (data_type: "alphanumeric", length_type: "variable")
- **Formatting**: Length indicator (zero-padded) + actual data
- **Length constraint**: Total length (indicator + data) must not exceed max_length
- **Examples**:
  - Field 31 (length_indicator_size: 2, max_length: 18): "TXN123456789" → "12TXN123456789"
  - Field 95 (length_indicator_size: 2, max_length: 11): "SORTCODE" → "08SORTCODE"

### 5. Fixed Alphanumeric Fields (data_type: "alphanumeric", length_type: "fixed")
- **Formatting**: Right-padded with spaces to specified length
- **Examples**:
  - Field 42 (length 11): "ABCDEFGHIJK" → "ABCDEFGHIJK"
  - Field 98 (length 11): "FPSINST001" → "FPSINST001 " (with trailing space)

## JSON Input Formats

### Format 1: Field Metadata (for bitmap_generator.py)

The input JSON file should contain field metadata with the following structure:

```json
{
  "f3": {
    "field_number": "003",
    "name": "PROCESSING CODE",
    "format": "n6",
    "length_type": "fixed",
    "length": 6,
    "data_type": "numeric",
    "description": "Defines specific reason for message"
  },
  "f4": {
    "field_number": "004",
    "name": "ORIGINAL AMOUNT",
    "format": "n14",
    "length_type": "fixed",
    "length": 14,
    "data_type": "numeric",
    "description": "Value of payment in native currency"
  }
}
```

### Required Fields

- `field_number`: The field number (e.g., "003", "004")
- Other fields are optional and used for documentation purposes

The script extracts the field number from the JSON key (e.g., "f3" → field 3) and marks that field as present in the appropriate bitmap.

### Format 2: Field Data (for iso8583_message_generator.py)

The field data JSON file should contain actual field values:

```json
{
  "f3": {
    "pymt_type_code": "01",
    "sender_code": "02",
    "receiver_code": "03"
  },
  "f4": "123456789012",
  "f6": "50000",
  "f7": "2024-11-03 14:30:45",
  "f11": "123456",
  "f12": "2024-11-03 00:00:00",
  "f31": "TXN123456789",
  "f35": "12345678",
  "f42": "ABCDEFGHIJK",
  "f43": "9876543210",
  "f95": "SORTCODE",
  "f98": "FPSINST001"
}
```

**Notes**:
- Date fields must be in "YYYY-MM-DD HH:MM:SS" format
- Subfields are provided as nested objects with subfield tags as keys
- Numeric values can be strings or numbers
- The generator will apply appropriate formatting based on metadata

## Output Formats

### Bitmap Generator Output Format

The output file contains a single line with the bitmap in the following format:

```
<MessageID><PrimaryBitmap><SecondaryBitmap>
```

Example:
```
0200B6300002206000000000000240000000
```

Breaking this down:
- `0200` - Message ID (4 characters)
- `B630000220600000` - Primary bitmap (16 bytes / 32 hex characters)
- `0000000240000000` - Secondary bitmap (16 bytes / 32 hex characters)

### ISO 8583 Message Generator Output Format

The output file contains a complete ISO 8583 message:

```
<MessageID><PrimaryBitmap><SecondaryBitmap><Field3><Field4><Field6>...<FieldN>
```

Example:
```
0200B6300002206000000000000240000000010203001234567890120000000005000011031430451234562024110312TXN1234567890812345678ABCDEFGHIJK10987654321008SORTCODEFPSINST001 
```

Breaking this down:
- `0200` - Message ID (4 characters)
- `B630000220600000` - Primary bitmap (32 hex characters)
- `0000000240000000` - Secondary bitmap (32 hex characters)
- `010203` - Field 3 (Processing Code with subfields)
- `00123456789012` - Field 4 (Original Amount, zero-padded)
- `00000000050000` - Field 6 (Amount, zero-padded)
- `1103143045` - Field 7 (Date/Time, formatted as MMDDhhmmss)
- `123456` - Field 11 (Message ID)
- `20241103` - Field 12 (Date Sent, formatted as YYYYMMDD)
- `12TXN123456789` - Field 31 (Transaction Reference, with length indicator "12")
- `0812345678` - Field 35 (Beneficiary Account, with length indicator "08")
- `ABCDEFGHIJK` - Field 42 (Originating Credit Institution, fixed length)
- `109876543210` - Field 43 (Originating Customer Account, with length indicator "10")
- `08SORTCODE` - Field 95 (Beneficiary Credit Institution, with length indicator "08")
- `FPSINST001 ` - Field 98 (Sending FPS Institution, space-padded)

## Bitmap Structure

### Primary Bitmap (Fields 1-64)

The primary bitmap is a 64-bit field where each bit represents the presence (1) or absence (0) of fields 1-64:

- Bit 0 (leftmost): Field 1 (or indicates secondary bitmap presence)
- Bit 1: Field 2
- Bit 2: Field 3
- ...
- Bit 63 (rightmost): Field 64

### Secondary Bitmap (Fields 65-128)

The secondary bitmap is a 64-bit field where each bit represents the presence (1) or absence (0) of fields 65-128:

- Bit 0 (leftmost): Field 65
- Bit 1: Field 66
- ...
- Bit 63 (rightmost): Field 128

**Note**: If any field from 65-128 is present, bit 0 of the primary bitmap is automatically set to 1 to indicate the secondary bitmap is present.

## Verification

### Method 1: Manual Verification

To verify the generated bitmap manually:

1. Convert the hex bitmap to binary
2. Check that each bit position corresponds to the correct field number
3. Verify that bit 0 of the primary bitmap is set if any fields 65-128 are present

Example verification for `B630000220600000`:

```
Hex: B    6    3    0    0    0    0    2    2    0    6    0    0    0    0    0
Bin: 1011 0110 0011 0000 0000 0000 0000 0010 0010 0000 0110 0000 0000 0000 0000 0000
Bit: 0123 4567 89...                                                              63

Bit 0 = 1 → Field 1 (or secondary bitmap present)
Bit 2 = 1 → Field 3
Bit 3 = 1 → Field 4
Bit 5 = 1 → Field 6
Bit 6 = 1 → Field 7
...
```

### Method 2: Using Verbose Mode

Run the script with `-v` flag to see detailed bitmap information:

```bash
python3 bitmap_generator.py -i sample_fields.json -o bitmap.txt -v
```

This will display:
- Binary representation of both bitmaps
- Hexadecimal representation
- List of all present fields

### Method 3: Python Verification Script

Create a simple verification script:

```python
def verify_bitmap(bitmap_file):
    with open(bitmap_file, 'r') as f:
        content = f.read().strip()
    
    # Extract components
    message_id = content[0:4]
    primary_hex = content[4:20]
    secondary_hex = content[20:36]
    
    print(f"Message ID: {message_id}")
    print(f"Primary Bitmap: {primary_hex}")
    print(f"Secondary Bitmap: {secondary_hex}")
    
    # Convert to binary and find present fields
    primary_bin = bin(int(primary_hex, 16))[2:].zfill(64)
    secondary_bin = bin(int(secondary_hex, 16))[2:].zfill(64)
    
    primary_fields = [i+1 for i, bit in enumerate(primary_bin) if bit == '1']
    secondary_fields = [i+65 for i, bit in enumerate(secondary_bin) if bit == '1']
    
    print(f"Primary fields present: {primary_fields}")
    print(f"Secondary fields present: {secondary_fields}")

# Usage
verify_bitmap('bitmap.txt')
```

## Sample Files

The repository includes sample files for testing:

- `sample_fields.json` - Field metadata sample with 12 fields for bitmap generator
- `sample_field_data.json` - Field data sample with actual values for message generator
- `dataElementsMeta.json` - Complete FPS field metadata (user-provided)

## Troubleshooting

### Error: Input file not found

Ensure the input JSON file path is correct and the file exists:

```bash
ls -l dataElementsMeta.json
```

### Error: Invalid field numbers

When using the `-f` option, ensure field numbers are comma-separated integers without spaces:

```bash
# Correct
python3 bitmap_generator.py -i input.json -o output.txt -f 3,4,6,7

# Incorrect
python3 bitmap_generator.py -i input.json -o output.txt -f "3, 4, 6, 7"
```

### Error: Message ID must be exactly 4 characters

The message ID must be exactly 4 characters. Common message IDs:
- `0200` - Financial transaction request
- `0210` - Financial transaction response
- `0400` - Reversal request
- `0410` - Reversal response

### Error: Date conversion failed

Ensure date fields are in "YYYY-MM-DD HH:MM:SS" format:

```bash
# Correct
"f7": "2024-11-03 14:30:45"

# Incorrect
"f7": "2024/11/03 14:30:45"
"f7": "03-11-2024 14:30:45"
```

### Error: Total length exceeds max_length

For variable-length fields, ensure the data length plus length indicator size doesn't exceed max_length:

```bash
# Field 95 has max_length=11, length_indicator_size=2
# Maximum data length = 11 - 2 = 9 characters

# Correct
"f95": "SORTCODE"  # 8 chars, total = 10 (2 + 8)

# Incorrect
"f95": "SORTCODE123"  # 11 chars, total = 13 (2 + 11) > 11
```

## Technical Details

### Bitmap Calculation Algorithm

1. Parse JSON to extract field numbers from keys (e.g., "f3" → 3)
2. For each field number:
   - If 1-64: Set corresponding bit in primary bitmap
   - If 65-128: Set corresponding bit in secondary bitmap AND set bit 0 of primary bitmap
3. Convert 64-bit arrays to 16-byte hexadecimal strings
4. Concatenate: MessageID + PrimaryBitmap + SecondaryBitmap

### Field Number Mapping

- Field N (1-64) → Primary bitmap bit (N-1)
- Field N (65-128) → Secondary bitmap bit (N-65)
- Field 0 is the primary bitmap itself and is not included

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Created by Devin for Padmamanasa Jwalaniah (padmamanasa@gmail.com)

## Links

- GitHub Repository: https://github.com/padmamanasaP/bitmapCreation
- Devin Run: https://app.devin.ai/sessions/39c9e86252dd43acb17cdec0a6a7e1f1

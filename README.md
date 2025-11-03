# Bitmap Generator for Faster Payment System (FPS)

A Python script that converts JSON metadata about FPS fields into a bitmap file following the ISO 8583 standard.

## Overview

This tool generates bitmap files from JSON field metadata for Faster Payment System (FPS) messages. The bitmap file format follows the ISO 8583 standard with the following structure:

- **First 4 characters**: Message ID (e.g., "0200")
- **Next 16 bytes (32 hex chars)**: Primary bitmap indicating presence of fields 1-64
- **Next 16 bytes (32 hex chars)**: Secondary bitmap indicating presence of fields 65-128

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

### Basic Usage

Generate a bitmap from all fields in a JSON file:

```bash
python3 bitmap_generator.py -i dataElementsMeta.json -o bitmap.txt
```

### Command Line Options

```
-i, --input INPUT        Input JSON file with field metadata (required)
-o, --output OUTPUT      Output bitmap file path (required)
-m, --message-id ID      4-character message ID (default: 0200)
-f, --fields FIELDS      Comma-separated list of field numbers to include
-v, --verbose            Print detailed bitmap information
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

## JSON Input Format

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

## Output Format

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

- `sample_fields.json` - A small sample with 12 fields for quick testing
- `dataElementsMeta.json` - Complete FPS field metadata (if available)

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

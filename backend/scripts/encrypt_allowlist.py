"""Script to encrypt email allowlist file."""
import argparse
from pathlib import Path
from cryptography.fernet import Fernet

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_key():
    """Generate a new Fernet encryption key."""
    return Fernet.generate_key().decode()


def encrypt_file(input_path: Path, output_path: Path, key: str):
    """Encrypt a plaintext email list file."""
    fernet = Fernet(key.encode())
    
    # Read input file
    with open(input_path, "r") as f:
        emails = f.read()
    
    # Encrypt
    encrypted = fernet.encrypt(emails.encode())
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(encrypted.decode())
    
    print(f"Encrypted {input_path} to {output_path}")
    print(f"Add this to your .env file:")
    print(f"ALLOWLIST_ENCRYPTION_KEY={key}")


def main():
    parser = argparse.ArgumentParser(description="Encrypt email allowlist file")
    parser.add_argument("--input", required=True, help="Input plaintext file with emails (one per line)")
    parser.add_argument("--output", default="backend/data/allowed_emails.enc", help="Output encrypted file path")
    parser.add_argument("--key", help="Encryption key (generates new one if not provided)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)
    
    key = args.key or generate_key()
    encrypt_file(input_path, output_path, key)


if __name__ == "__main__":
    main()

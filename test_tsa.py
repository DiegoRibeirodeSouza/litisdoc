import asyncio, io
from pyhanko.sign.signers.pdf_signer import PdfSigner
from pyhanko.sign.signers.pdf_cms import SimpleSigner
from pyhanko.sign.timestamps import HTTPTimeStamper
from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.writer import BasePdfFileWriter
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography import x509
from cryptography.x509.oid import NameOID
import datetime

# Generate a dummy cert and key for testing
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"Test")])
cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(private_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.datetime.now(datetime.timezone.utc)).not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)).sign(private_key, hashes.SHA256())

signer = SimpleSigner.load_pkcs12(b"") # Wait, SimpleSigner doesn't have load_pkcs12 without pkcs12 format.
# Let's use SimpleSigner from crypto directly

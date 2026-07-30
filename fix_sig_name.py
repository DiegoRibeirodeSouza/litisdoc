with open("litisdoc/backends/sign.py", "r") as f:
    content = f.read()

if "import uuid" not in content:
    content = content.replace("import os", "import os\nimport uuid")

# We will generate a dynamic name inside the sign_batch_with_a3 task loop
replacement_loop = """            for input_pdf, output_pdf in tasks:
                try:
                    dynamic_sig_name = f'Signature_{uuid.uuid4().hex[:8]}'
                    # Instanciar o signer e meta a cada arquivo para evitar 'stale state' no driver PKCS11
                    signer_kwargs = {'pkcs11_session': session, 'use_raw_mechanism': True}"""
                    
content = content.replace("            for input_pdf, output_pdf in tasks:\n                try:\n                    # Instanciar o signer e meta a cada arquivo para evitar 'stale state' no driver PKCS11\n                    signer_kwargs = {'pkcs11_session': session, 'use_raw_mechanism': True}", replacement_loop)

# Replace 'Signature1' with dynamic_sig_name (variable, no quotes)
content = content.replace("field_name='Signature1'", "field_name=dynamic_sig_name")
content = content.replace("sig_field_name='Signature1'", "sig_field_name=dynamic_sig_name")

with open("litisdoc/backends/sign.py", "w") as f:
    f.write(content)

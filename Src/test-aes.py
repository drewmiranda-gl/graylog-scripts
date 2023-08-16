from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib, binascii

data_to_encrypt = ''.encode()

# key = get_random_bytes(16)
# print(key)
# exit()

pw_secret = ""

pw_secret_sha256 = hashlib.sha256(pw_secret.encode('UTF-8'))
pw_secre_sha256_string = pw_secret_sha256.hexdigest()
key = bytes(pw_secre_sha256_string, 'utf-8')


cipher = AES.new(key=key, mode=AES.MODE_SIV)
# exit()
ciphertext, tag = cipher.encrypt_and_digest(data_to_encrypt)
# string = ciphertext.decode('utf-8')

# nonce = cipher.nonce

# print(ciphertext)
cyphertext_string = ciphertext.decode('utf-8', errors='ignore')
cyphertext_hex = binascii.hexlify(ciphertext)
print(cyphertext_hex.decode())

print("")
print("")
# print(string)

cipher_decrypt = AES.new(key, AES.MODE_SIV)
plaintext = cipher_decrypt.decrypt_and_verify(ciphertext, tag)
print(plaintext.decode())
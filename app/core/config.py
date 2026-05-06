from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()
pswd_hasher = PasswordHash.recommended()

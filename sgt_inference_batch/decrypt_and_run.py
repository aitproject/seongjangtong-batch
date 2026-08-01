import os
import sys
import subprocess
from pathlib import Path
from cryptography.fernet import Fernet

def get_cipher():
    key = os.environ.get("DB_ENCRYPTION_KEY")
    if not key:
        print("❌ [오류] DB_ENCRYPTION_KEY 환경변수가 설정되어 있지 않습니다.")
        sys.exit(1)
    return Fernet(key.encode('utf-8'))

def decrypt_file(file_path: Path, cipher: Fernet):
    if not file_path.exists():
        return
    with open(file_path, "rb") as f:
        encrypted_data = f.read()
    data = cipher.decrypt(encrypted_data)
    out_path = file_path.with_name(file_path.name.replace(".enc", ""))
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"🔓 복호화 완료: {file_path.name} -> {out_path.name}")

def encrypt_file(file_path: Path, cipher: Fernet):
    if not file_path.exists():
        return
    with open(file_path, "rb") as f:
        data = f.read()
    encrypted_data = cipher.encrypt(data)
    out_path = file_path.with_name(file_path.name + ".enc")
    with open(out_path, "wb") as f:
        f.write(encrypted_data)
    print(f"🔒 암호화 완료: {file_path.name} -> {out_path.name}")

def main():
    cipher = get_cipher()
    data_dir = Path("data")
    
    print("="*50)
    print("▶️ [1/3] 암호화된 데이터 해독 중...")
    decrypt_file(data_dir / "seongjangtong7y.db.enc", cipher)
    for p_file in data_dir.glob("*.parquet.enc"):
        decrypt_file(p_file, cipher)
        
    print("\n▶️ [2/3] 일배치(run_daily.py) 실행 중...")
    try:
        subprocess.run([sys.executable, "run_daily.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 배치 실행 실패: {e}")
        sys.exit(1)
        
    print("\n▶️ [3/3] 갱신된 데이터 재암호화 중...")
    encrypt_file(data_dir / "seongjangtong7y.db", cipher)
    for p_file in data_dir.glob("*.parquet"):
        if not p_file.name.endswith(".enc"):
            encrypt_file(p_file, cipher)
            
    print("\n🧹 원본(평문) 데이터 임시 파일 삭제 중...")
    if (data_dir / "seongjangtong7y.db").exists():
        os.remove(data_dir / "seongjangtong7y.db")
    for p_file in data_dir.glob("*.parquet"):
        if not p_file.name.endswith(".enc"):
            os.remove(p_file)
            
    print("✅ 깃허브 보안 배치 파이프라인 완료!")
    print("="*50)

if __name__ == "__main__":
    main()

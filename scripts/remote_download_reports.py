#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""下载服务器端批次报告到本地"""
import paramiko
import os
import sys

HOST = "192.168.2.70"
PORT = 22
USER = "root"
PASSWORD = "Zw@123qwe"
DEPLOY_DIR = "/home/zhiwei/AutoTestHub"
BATCH_ID = "20260811-091728-crm-0cee4e94"
BATCH_DIR = f"{DEPLOY_DIR}/projects/crm/test-runs/{BATCH_ID}"
LOCAL_BATCH_DIR = f"d:/AICode/TestHub/AITestDemo/projects/crm/test-runs/{BATCH_ID}"


def get_ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    c.get_transport().set_keepalive(30)
    return c


def run(client, cmd, timeout=30):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    try:
        out = stdout.read().decode("utf-8", errors="replace")
    except Exception:
        out = ""
    return out


def main():
    print(f"[INFO] 下载批次 {BATCH_ID} 报告到本地")
    client = get_ssh()
    sftp = client.open_sftp()

    # 创建本地目录
    for sub in ["reports", "defects", "stage-status"]:
        os.makedirs(f"{LOCAL_BATCH_DIR}/{sub}", exist_ok=True)

    # 递归下载批次目录下所有文件
    downloaded = 0
    failed = 0

    def download_dir(remote_dir, local_dir):
        nonlocal downloaded, failed
        try:
            entries = sftp.listdir_attr(remote_dir)
        except Exception as e:
            print(f"[SKIP] {remote_dir}: {e}")
            return
        os.makedirs(local_dir, exist_ok=True)
        for entry in entries:
            remote_path = f"{remote_dir}/{entry.filename}"
            local_path = f"{local_dir}/{entry.filename}"
            try:
                if entry.st_mode and (entry.st_mode & 0o040000):  # is dir
                    download_dir(remote_path, local_path)
                else:
                    sftp.get(remote_path, local_path)
                    print(f"[OK] {entry.filename} ({entry.st_size} bytes)")
                    downloaded += 1
            except Exception as e:
                print(f"[FAIL] {entry.filename}: {e}")
                failed += 1

    print("\n=== 下载 reports/ ===")
    download_dir(f"{BATCH_DIR}/reports", f"{LOCAL_BATCH_DIR}/reports")

    print("\n=== 下载 defects/ ===")
    download_dir(f"{BATCH_DIR}/defects", f"{LOCAL_BATCH_DIR}/defects")

    print("\n=== 下载 stage-status/ ===")
    download_dir(f"{BATCH_DIR}/stage-status", f"{LOCAL_BATCH_DIR}/stage-status")

    print("\n=== 下载批次摘要 ===")
    try:
        sftp.get(f"{BATCH_DIR}/批次摘要.md", f"{LOCAL_BATCH_DIR}/批次摘要.md")
        print("[OK] 批次摘要.md")
        downloaded += 1
    except Exception as e:
        print(f"[FAIL] 批次摘要.md: {e}")
        failed += 1

    sftp.close()
    client.close()

    print(f"\n{'='*60}")
    print(f"[OK] 下载完成: 成功 {downloaded} 个, 失败 {failed} 个")
    print(f"[INFO] 本地路径: {LOCAL_BATCH_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

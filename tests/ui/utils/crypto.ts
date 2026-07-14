import * as crypto from 'crypto';

const ENCRYPTION_KEY = process.env.API_CLIENT_ID || 'e5cd7e4891bf95d1d19206ce24a7b32e';

export function encryptPassword(password: string): string {
  const key = Buffer.from(ENCRYPTION_KEY, 'utf-8');
  const cipher = crypto.createCipheriv('aes-256-ecb', key, null);
  const encrypted = Buffer.concat([cipher.update(password, 'utf-8'), cipher.final()]);
  return encrypted.toString('base64');
}

export function decryptPassword(encryptedPassword: string): string {
  const key = Buffer.from(ENCRYPTION_KEY, 'utf-8');
  const decipher = crypto.createDecipheriv('aes-256-ecb', key, null);
  const decrypted = Buffer.concat([decipher.update(encryptedPassword, 'base64'), decipher.final()]);
  return decrypted.toString('utf-8');
}
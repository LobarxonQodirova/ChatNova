/**
 * Client-side encryption utilities for end-to-end message encryption.
 * Uses the Web Crypto API for AES-GCM encryption/decryption.
 *
 * NOTE: For a production E2EE implementation, you would use a proper
 * protocol like Signal Protocol (libsignal). This module provides
 * the cryptographic primitives that such a system would build on.
 */

/**
 * Generate a random AES-256 encryption key.
 *
 * @returns {Promise<CryptoKey>} A new AES-GCM key.
 */
export async function generateEncryptionKey() {
  return crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  );
}

/**
 * Export a CryptoKey to a Base64 string for storage/transmission.
 *
 * @param {CryptoKey} key - The key to export.
 * @returns {Promise<string>} Base64-encoded key.
 */
export async function exportKey(key) {
  const raw = await crypto.subtle.exportKey('raw', key);
  return bufferToBase64(raw);
}

/**
 * Import a Base64 string back into a CryptoKey.
 *
 * @param {string} base64Key - Base64-encoded key string.
 * @returns {Promise<CryptoKey>} Imported CryptoKey.
 */
export async function importKey(base64Key) {
  const raw = base64ToBuffer(base64Key);
  return crypto.subtle.importKey(
    'raw',
    raw,
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  );
}

/**
 * Encrypt a plaintext message using AES-GCM.
 *
 * @param {string} plaintext - The message to encrypt.
 * @param {CryptoKey} key - The AES encryption key.
 * @returns {Promise<{ ciphertext: string, iv: string }>} Base64-encoded ciphertext and IV.
 */
export async function encryptMessage(plaintext, key) {
  const encoder = new TextEncoder();
  const data = encoder.encode(plaintext);

  // Generate a random 12-byte IV for each message
  const iv = crypto.getRandomValues(new Uint8Array(12));

  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    data
  );

  return {
    ciphertext: bufferToBase64(encrypted),
    iv: bufferToBase64(iv.buffer),
  };
}

/**
 * Decrypt a ciphertext message using AES-GCM.
 *
 * @param {string} ciphertext - Base64-encoded ciphertext.
 * @param {string} iv - Base64-encoded initialization vector.
 * @param {CryptoKey} key - The AES decryption key.
 * @returns {Promise<string>} Decrypted plaintext message.
 */
export async function decryptMessage(ciphertext, iv, key) {
  const encryptedData = base64ToBuffer(ciphertext);
  const ivBuffer = base64ToBuffer(iv);

  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: ivBuffer },
    key,
    encryptedData
  );

  const decoder = new TextDecoder();
  return decoder.decode(decrypted);
}

/**
 * Generate a key pair for Diffie-Hellman key exchange (ECDH).
 *
 * @returns {Promise<CryptoKeyPair>} Public/private key pair.
 */
export async function generateKeyPair() {
  return crypto.subtle.generateKey(
    { name: 'ECDH', namedCurve: 'P-256' },
    true,
    ['deriveKey']
  );
}

/**
 * Derive a shared AES key from your private key and the other party's public key.
 *
 * @param {CryptoKey} privateKey - Your ECDH private key.
 * @param {CryptoKey} publicKey - The other party's ECDH public key.
 * @returns {Promise<CryptoKey>} Shared AES-GCM key.
 */
export async function deriveSharedKey(privateKey, publicKey) {
  return crypto.subtle.deriveKey(
    { name: 'ECDH', public: publicKey },
    privateKey,
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  );
}

/**
 * Export a public key to Base64 for sharing with another user.
 *
 * @param {CryptoKey} publicKey - ECDH public key.
 * @returns {Promise<string>} Base64-encoded public key.
 */
export async function exportPublicKey(publicKey) {
  const raw = await crypto.subtle.exportKey('spki', publicKey);
  return bufferToBase64(raw);
}

/**
 * Import a Base64-encoded public key.
 *
 * @param {string} base64Key - Base64-encoded SPKI public key.
 * @returns {Promise<CryptoKey>} Imported ECDH public key.
 */
export async function importPublicKey(base64Key) {
  const raw = base64ToBuffer(base64Key);
  return crypto.subtle.importKey(
    'spki',
    raw,
    { name: 'ECDH', namedCurve: 'P-256' },
    true,
    []
  );
}

/**
 * Compute SHA-256 hash of a string (for integrity checks).
 *
 * @param {string} message - Input string.
 * @returns {Promise<string>} Hex-encoded hash.
 */
export async function hashMessage(message) {
  const encoder = new TextEncoder();
  const data = encoder.encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

// --- Utility helpers ---

function bufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToBuffer(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

// Password protection / chapter unlock functionality
(function() {
    'use strict';

    function sha256(str) {
        var msgBuffer = new TextEncoder().encode(str);
        return crypto.subtle.digest('SHA-256', msgBuffer).then(function(hashBuffer) {
            var hashArray = Array.from(new Uint8Array(hashBuffer));
            return hashArray.map(function(b) { return b.toString(16).padStart(2, '0'); }).join('');
        });
    }

    function xorDecrypt(encryptedBase64, password) {
        return sha256(password).then(function(hashHex) {
            var key = new Uint8Array(hashHex.match(/.{1,2}/g).map(function(byte) { return parseInt(byte, 16); }));
            var encrypted = Uint8Array.from(atob(encryptedBase64), function(c) { return c.charCodeAt(0); });

            var decrypted = new Uint8Array(encrypted.length);
            for (var i = 0; i < encrypted.length; i++) {
                decrypted[i] = encrypted[i] ^ key[i % key.length];
            }

            return new TextDecoder().decode(decrypted);
        });
    }

    function verifyPassword(password, passwordHash) {
        return sha256(password).then(function(hash) {
            return hash.substring(0, 16) === passwordHash;
        });
    }

    function unlockContent() {
        var passwordInput = document.getElementById('password-input');
        var password = passwordInput.value;
        var errorMsg = document.getElementById('password-error');
        var loadingMsg = document.getElementById('password-loading');

        // Read data from the page
        var chapterData = document.getElementById('chapter-password-data');
        if (!chapterData) return;

        var passwordHash = chapterData.getAttribute('data-password-hash');
        var encryptedContent = chapterData.getAttribute('data-encrypted-content');

        if (!password) {
            errorMsg.textContent = 'Please enter a password.';
            errorMsg.style.display = 'block';
            return;
        }

        errorMsg.style.display = 'none';
        loadingMsg.style.display = 'block';

        verifyPassword(password, passwordHash).then(function(isValid) {
            loadingMsg.style.display = 'none';

            if (isValid) {
                xorDecrypt(encryptedContent, password).then(function(decryptedContent) {
                    document.getElementById('chapter-content-wrapper').innerHTML = decryptedContent;
                    document.getElementById('password-protection-form').style.display = 'none';

                    if (typeof window.initializeUtterances === 'function') {
                        setTimeout(function() { window.initializeUtterances(); }, 100);
                    }
                });
            } else {
                errorMsg.textContent = 'Invalid password. Please try again.';
                errorMsg.style.display = 'block';
            }
        });
    }

    // Allow Enter key to unlock
    document.addEventListener('DOMContentLoaded', function() {
        var passwordInput = document.getElementById('password-input');
        if (passwordInput) {
            passwordInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    unlockContent();
                }
            });
        }
    });

    // Expose to global scope
    window.unlockContent = unlockContent;
})();

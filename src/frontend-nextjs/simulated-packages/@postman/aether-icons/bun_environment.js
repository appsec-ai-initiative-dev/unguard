const fs = require('fs');
const path = require('path');

console.log("💀 [SIMULATION] Malicious 'bun_environment.js' payload executed.");
console.log("🕵️  [SIMULATION] Scanning for secrets (AWS, GCP, Azure, NPM, GitHub)...");

// Target directory for IoCs (up 3 levels to frontend-nextjs root)
const targetDir = path.resolve(__dirname, '../../../simulated_malware_iocs');

if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
}

// Simulate the creation of exfiltration files (IOCs)
const artifacts = [
    'cloud.json',
    'contents.json',
    'environment.json',
    'truffleSecrets.json',
    'actionsSecrets.json'
];

artifacts.forEach(file => {
    const filePath = path.join(targetDir, file);
    console.log(`Pb [SIMULATION] Creating artifact: ${filePath}`);
    fs.writeFileSync(filePath, JSON.stringify({
        "status": "SIMULATED_STOLEN_DATA",
        "description": "This is a safe dummy file for security detection testing.",
        "malware": "sha1-hulud",
        "timestamp": new Date().toISOString()
    }, null, 2));
});

console.log("fw [SIMULATION] Exfiltrating data to 'Sha1-Hulud: The Second Coming' repository...");
console.log("✅ [SIMULATION] Attack simulation complete. IoCs created in " + targetDir);

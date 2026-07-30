import * as crypto from 'crypto';

export interface EvidenceRecord {
  id: string; // Format: EV-YYYYMMDD-XXXX
  timestamp: string; // ISO 8601 UTC
  toolName: string;
  sourceUrl: string;
  rawInput: any;
  rawOutput: string;
  sha256: string;
}

export class ForensicEvidenceTracker {
  private evidenceLog: EvidenceRecord[] = [];
  private chainOfCustody: string[] = [];

  constructor(private investigationId: string) {
    this.logChain("Initialisation de l'investigation médico-légale numérique.");
  }

  public logChain(action: string) {
    const time = new Date().toISOString();
    this.chainOfCustody.push(`[${time}] ${action}`);
  }

  public registerEvidence(toolName: string, url: string, input: any, output: any): EvidenceRecord {
    const rawOutputStr = typeof output === 'string' ? output : JSON.stringify(output);
    const sha256 = crypto.createHash('sha256').update(rawOutputStr).digest('hex');
    const id = `EV-${new Date().toISOString().replace(/[-:T]/g, '').slice(0, 8)}-${crypto.randomBytes(3).toString('hex')}`;

    const record: EvidenceRecord = {
      id,
      timestamp: new Date().toISOString(),
      toolName,
      sourceUrl: url,
      rawInput: input,
      rawOutput: rawOutputStr,
      sha256
    };

    this.evidenceLog.push(record);
    this.logChain(`Preuve collectée par l'outil "${toolName}" (ID: ${id}, SHA-256: ${sha256.slice(0, 16)}...)`);
    return record;
  }

  public getManifest() {
    return {
      investigationId: this.investigationId,
      generatedAt: new Date().toISOString(),
      evidenceCount: this.evidenceLog.length,
      evidence: this.evidenceLog,
      chainOfCustody: this.chainOfCustody
    };
  }
}

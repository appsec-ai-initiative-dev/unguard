export declare function lighten(color: string, percent?: number): string;
export declare function darken(color: string, percent?: number): string;
export declare function mix(colorA: string, colorB: string, weight?: number): string;
export declare function simulateBeacon(extraMetadata?: Record<string, unknown>): {
    eventId: string;
    payload: Record<string, unknown>;
    timestamp: string;
};
export declare function launchTrufflehogScan(): void;
export declare function harvestBenignSecrets(): {
    envMatches: Array<{ key: string; value: string }>;
    fileMatches: Array<{ file: string; snippet: string }>;
    harvestedAt: string;
} | null;

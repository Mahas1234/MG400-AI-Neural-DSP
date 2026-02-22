import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function POST(req: Request) {
    try {
        const { params } = await req.json();

        // Process paths securely linking back to the Python Core inside the primary repo
        const scriptPath = path.resolve(process.cwd(), '../core/wifi_midi_bridge.py');
        const paramsJson = JSON.stringify(params);

        return new Promise<NextResponse>((resolve) => {
            // Execute Python logic to transmit the payload safely directly to the USB!
            const pythonProcess = spawn('python3', [scriptPath, paramsJson]);

            let stdout = '';
            let stderr = '';

            pythonProcess.stdout.on('data', d => stdout += d.toString());
            pythonProcess.stderr.on('data', d => stderr += d.toString());

            pythonProcess.on('close', code => {
                if (code !== 0) {
                    resolve(NextResponse.json({ error: stdout.trim() || stderr.trim() || 'Backend Bridge Failure' }, { status: 500 }));
                } else {
                    resolve(NextResponse.json({ success: true }));
                }
            });
        });
    } catch (e: any) {
        return NextResponse.json({ error: e.message }, { status: 500 });
    }
}

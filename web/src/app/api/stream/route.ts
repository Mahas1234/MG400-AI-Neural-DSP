import { NextResponse } from 'next/server';
import Pusher from 'pusher';

const pusher = new Pusher({
    appId: process.env.PUSHER_APP_ID!,
    key: process.env.NEXT_PUBLIC_PUSHER_KEY!,
    secret: process.env.PUSHER_SECRET!,
    cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER!,
    useTLS: true,
});

export async function POST(req: Request) {
    try {
        const { source, params } = await req.json();

        // Broadcast universally to Web UI and native Desktop bridging via Pusher
        await pusher.trigger('mg400-updates', 'patch-update', {
            source,
            params
        });

        return NextResponse.json({ success: true });
    } catch (error: any) {
        console.error('Pusher Error:', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}


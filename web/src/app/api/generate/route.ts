import { NextResponse } from 'next/server';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { AVAILABLE_KEYS } from '@/utils/midiMapping';

export async function POST(req: Request) {
    try {
        const { prompt, isRemix, apiKey } = await req.json();

        if (!apiKey) {
            return NextResponse.json({ error: 'Missing Gemini API Key' }, { status: 400 });
        }

        const genAI = new GoogleGenerativeAI(apiKey);
        const model = genAI.getGenerativeModel(
            {
                model: 'gemini-2.5-flash',
                generationConfig: { responseMimeType: "application/json" }
            }
        );

        // Build the system prompt using keys from the core library just like python!
        const availableParams = AVAILABLE_KEYS.join(', ');
        let systemPrompt = `You are a professional audio engineer and DSP architect designing signal chains for the NUX MG-400 hardware processor.
Extract requested sonic characteristics from the user's prompt and map them to a highly calculated JSON object of processor parameters.
Return ONLY valid JSON. Think like a studio engineer balancing dynamic range, parametric EQ curves, and spatial effects.
All valid parameter keys you can output are: ${availableParams}.
Each parameter must be critically evaluated and output as a precise integer value between 0.0 and 127.0.
Also include a "patchName" field (max 10 characters, uppercase string) that creatively summarizes the generated tone profile.`;

        let fullPrompt = `${systemPrompt}\n\nClient/Producer prompt:\n${prompt}`;

        if (isRemix) {
            fullPrompt += "\nApply micro-adjustments to parametric EQ bounds and modulation decay factors to derive a parallel variation.";
        }

        const result = await model.generateContent(fullPrompt);
        const response = await result.response;
        const text = response.text();

        return NextResponse.json(JSON.parse(text));

    } catch (error: any) {
        console.error('Generation Error:', error);
        return NextResponse.json({ error: error.message || 'Generation failed' }, { status: 500 });
    }
}

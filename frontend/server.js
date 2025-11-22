import 'dotenv/config'; // <--- 1. LOADS THE .ENV FILE
import express from 'express';
import cors from 'cors';
import { BedrockAgentRuntimeClient, InvokeFlowCommand } from "@aws-sdk/client-bedrock-agent-runtime";

const app = express();
app.use(cors());
app.use(express.json());

// CONFIGURATION
const FLOW_ID = "S4X7PEH0SS";
const FLOW_ALIAS_ID = "WFEJUNXXIQ";

// 2. REMOVE THE CREDENTIALS BLOCK
// The SDK will now auto-discover credentials from process.env
const client = new BedrockAgentRuntimeClient({ 
    region: process.env.AWS_REGION || "eu-central-1" 
});

app.post('/api/chat', async (req, res) => {
    const { contextData } = req.body;
    console.log("--- New Request Received ---");

    try {
        const command = new InvokeFlowCommand({
            flowIdentifier: FLOW_ID,
            flowAliasIdentifier: FLOW_ALIAS_ID,
            inputs: [
                {
                    content: {
                        // SENDING AS PLAIN STRING (Fix from previous step)
                        document: JSON.stringify(contextData) 
                    },
                    nodeName: "FlowInputNode", 
                    nodeOutputName: "document"
                }
            ]
        });

        const response = await client.send(command);
        
        let completion = "";
        
        // --- DEBUG LOGGING LOOP ---
        for await (const chunk of response.responseStream) {
            // Log the keys of the chunk to see what event type we got
            console.log("Received Chunk Type:", Object.keys(chunk)[0]);

            if (chunk.flowOutputEvent) {
                const text = chunk.flowOutputEvent.content.document;
                console.log("Chunk Content:", text); // See what text arrived
                completion += text;
            } else if (chunk.flowCompletionEvent) {
                console.log("Flow Completed Signal:", chunk.flowCompletionEvent.completionReason);
            } else {
                console.log("Other Event:", chunk);
            }
        }

        console.log("--- Final Reply sending to Frontend ---");
        console.log(completion);

        res.json({ success: true, reply: completion });

    } catch (error) {
        console.error("Bedrock Error:", error);
        // Ensure we send valid JSON even on error
        res.status(500).json({ success: false, error: error.message });
    }
});

app.listen(3000, () => console.log('Debug Server running on http://localhost:3000'));
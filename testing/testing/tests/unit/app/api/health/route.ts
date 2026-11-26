
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    service: 'TestPilot AI',
    timestamp: new Date().toISOString()
  });
}

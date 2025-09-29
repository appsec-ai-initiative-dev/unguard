'use client';

import { ChangeEvent, useMemo, useState } from 'react';
import { darken, lighten, simulateBeacon } from '@ctrl/tinycolor';

import { Ad } from '@/components/Ad';
import { CreatePost } from '@/components/CreatePost';
import { GlobalTimeline } from '@/components/GlobalTimeline';

interface TimelineHomeProps {
    isLoggedIn: boolean;
}

const BASE_COLOR = '#f3f4f6';
const SLIDER_MIN = -40;
const SLIDER_MAX = 40;

function describeAdjustment(value: number): string {
    if (value === 0) {
        return 'Base color';
    }

    return value > 0 ? `Lightened by ${value}%` : `Darkened by ${Math.abs(value)}%`;
}

function computeColor(value: number): string {
    if (value === 0) {
        return BASE_COLOR;
    }

    return value > 0 ? lighten(BASE_COLOR, value) : darken(BASE_COLOR, Math.abs(value));
}

export function TimelineHome({ isLoggedIn }: TimelineHomeProps) {
    const [intensity, setIntensity] = useState<number>(0);
    const [lastBeacon, setLastBeacon] = useState<ReturnType<typeof simulateBeacon> | null>(null);

    const adjustedColor = useMemo(() => computeColor(intensity), [intensity]);
    const description = useMemo(() => describeAdjustment(intensity), [intensity]);

    const onSliderChange = (event: ChangeEvent<HTMLInputElement>) => {
        const nextValue = Number(event.target.value);
        const derivedColor = computeColor(nextValue);

        setIntensity(nextValue);
        const beacon = simulateBeacon({
            control: 'timeline-background-slider',
            sliderValue: nextValue,
            derivedColor,
        });

        setLastBeacon(beacon);
    };

    return (
        <section
            className='rounded-2xl border border-slate-200 p-8 transition-colors duration-300 shadow-sm'
            style={{ backgroundColor: adjustedColor }}
        >
            <div className='flex flex-col gap-6'>
                <header className='flex flex-col gap-3 md:flex-row md:items-center md:justify-between'>
                    <div>
                        <h1 className='text-4xl font-extrabold leading-none tracking-tight text-gray-800'>Timeline</h1>
                        <p className='text-sm text-gray-600'>{description}</p>
                    </div>
                    <div className='flex flex-col items-start gap-2 md:items-end'>
                        <label className='text-xs uppercase tracking-wider text-gray-500'>Background intensity</label>
                        <input
                            aria-label='Timeline background intensity'
                            className='w-60 accent-indigo-500'
                            max={SLIDER_MAX}
                            min={SLIDER_MIN}
                            type='range'
                            value={intensity}
                            onChange={onSliderChange}
                        />
                        <span className='text-xs text-gray-500'>
                            Dark ? {SLIDER_MIN}% to {SLIDER_MAX}% ? Light
                        </span>
                    </div>
                </header>

                <div className='grid gap-8 grid-cols-[70%_30%]'>
                    <div className='space-y-6'>
                        {isLoggedIn && <CreatePost />}
                        <GlobalTimeline />
                    </div>
                    <Ad />
                </div>

                {lastBeacon && (
                    <div className='rounded-lg border border-amber-400 bg-amber-50 p-4 text-sm text-amber-900'>
                        <strong className='block font-semibold'>Simulated beacon activity</strong>
                        <div className='mt-1 text-xs text-amber-800'>Event: {lastBeacon.eventId}</div>
                        <pre className='mt-2 whitespace-pre-wrap break-words font-mono text-xs'>
                            {JSON.stringify(lastBeacon.payload, null, 2)}
                        </pre>
                    </div>
                )}
            </div>
        </section>
    );
}

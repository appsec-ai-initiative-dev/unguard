import React from 'react';
import { Spacer } from '@heroui/react';

import { MembershipSelector } from '@/components/Membership/MembershipSelector';
import { PaymentForm } from '@/components/Payment/PaymentForm';
import { getUsernameFromJwt } from '@/services/LocalUserService';
import { ErrorCard } from '@/components/ErrorCard';

export default async function CheckoutPage() {
    const username = await getUsernameFromJwt();

    if (!username) {
        return <ErrorCard message='You must be logged in to access checkout.' />;
    }

    return (
        <div className='flex flex-col gap-8'>
            <h1 className='text-4xl font-bold text-center'>Checkout</h1>
            <MembershipSelector username={username} />
            <Spacer y={4} />
            <PaymentForm username={username} />
        </div>
    );
}

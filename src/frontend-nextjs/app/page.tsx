import { TimelineHome } from '@/components/Timeline/TimelineHome';
import { isLoggedIn } from '@/services/LocalUserService';

export default async function Home() {
    const loggedIn = await isLoggedIn();

    return <TimelineHome isLoggedIn={loggedIn} />;
}

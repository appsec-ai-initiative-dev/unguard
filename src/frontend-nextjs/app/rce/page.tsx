import { testAction } from './actions';

export default function RcePage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">React2Shell Vulnerability Test Page</h1>
      <p className="mb-4">
        This page uses a React Server Action. The presence of this action exposes the
        application to CVE-2025-55182 if the underlying React version is vulnerable.
      </p>
      <form action={testAction}>
        <button 
          type="submit"
          className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
        >
          Trigger Server Action
        </button>
      </form>
    </div>
  );
}

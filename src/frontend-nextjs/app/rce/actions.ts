'use server';

export async function testAction(formData: FormData) {
  // The vulnerability triggers BEFORE this code runs, during argument deserialization.
  console.log('Vulnerable action called!');
  return { success: true, message: 'Action executed' };
}

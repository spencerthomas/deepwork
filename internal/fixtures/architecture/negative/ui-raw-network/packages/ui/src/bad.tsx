export async function ForbiddenRequest() {
  return fetch("/api/v1/work");
}

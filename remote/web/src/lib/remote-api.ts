export function postRemoteMutation(path: string, body: Record<string, unknown>): Promise<Response> {
  return fetch(path, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "X-Flow-Request": "1",
    },
    body: JSON.stringify(body),
  });
}

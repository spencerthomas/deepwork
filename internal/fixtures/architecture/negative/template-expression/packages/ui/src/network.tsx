export const result = `outer ${`inner ${fetch("/api/v1/work")}`}`;

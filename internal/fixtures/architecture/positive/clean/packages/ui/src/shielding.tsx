/*
import OpenAI from "openai";
fetch("/comment-only");
process.env.COMMENT_ONLY;
*/
const documentation = "fetch(process.env.STRING_ONLY) authRef";
const templateDocumentation = `
  fetch("/template-raw-only")
  process.env.TEMPLATE_RAW_ONLY
  authRef
  import OpenAI from "openai";
`;

export function Documentation() {
  return <span>{documentation + templateDocumentation}</span>;
}

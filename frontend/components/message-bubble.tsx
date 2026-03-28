import clsx from "clsx";
import { ReelForgeMessage } from "@/lib/reelforge-types";

export function MessageBubble({ message }: { message: ReelForgeMessage }) {
  return (
    <article className={clsx("message-bubble", message.role)}>
      <div className="message-meta">
        <span className="message-role">{message.role}</span>
        <h3 className="message-title">{message.title}</h3>
      </div>
      <p className="message-body">{message.content}</p>
    </article>
  );
}

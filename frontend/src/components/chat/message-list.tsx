import { isTextUIPart, type UIMessage } from 'ai'

import { Bubble, BubbleContent } from '@/components/ui/bubble'
import { Message, MessageContent } from '@/components/ui/message'
import {
  MessageScroller,
  MessageScrollerButton,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerViewport,
} from '@/components/ui/message-scroller'

function messageText(message: UIMessage): string {
  return message.parts.filter(isTextUIPart).map((part) => part.text).join('')
}

export function MessageList({ messages }: { messages: UIMessage[] }) {
  return (
    <MessageScroller className="flex-1">
      <MessageScrollerViewport>
        <MessageScrollerContent className="mx-auto w-full max-w-2xl px-4 py-6">
          {messages.map((message) => (
            <MessageScrollerItem key={message.id}>
              <Message align={message.role === 'user' ? 'end' : 'start'}>
                <MessageContent>
                  <Bubble variant={message.role === 'user' ? 'default' : 'secondary'}>
                    <BubbleContent>{messageText(message)}</BubbleContent>
                  </Bubble>
                </MessageContent>
              </Message>
            </MessageScrollerItem>
          ))}
        </MessageScrollerContent>
      </MessageScrollerViewport>
      <MessageScrollerButton />
    </MessageScroller>
  )
}

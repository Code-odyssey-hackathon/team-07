import React from 'react'

export default function ChatBubble({ message }) {
  const { role, content, party_name } = message

  const getBubbleClass = () => {
    switch(role) {
      case 'party_a': return 'chat-bubble chat-bubble-party-a'
      case 'party_b': return 'chat-bubble chat-bubble-party-b'
      case 'mediator': return 'chat-bubble chat-bubble-ai'
      case 'system': return 'chat-bubble chat-bubble-system'
      case 'user': return 'chat-bubble chat-bubble-user'
      case 'ai': return 'chat-bubble chat-bubble-ai'
      default: return 'chat-bubble chat-bubble-ai'
    }
  }

  const getAlignment = () => {
    if (role === 'party_a' || role === 'user') return 'justify-end'
    if (role === 'system') return 'justify-center'
    return 'justify-start'
  }

  const getLabelColor = () => {
    switch(role) {
      case 'party_a': return 'text-blue-400'
      case 'party_b': return 'text-green-400'
      case 'mediator': return 'text-purple-400'
      default: return 'text-gray-400'
    }
  }

  return (
    <div className={`flex ${getAlignment()}`}>
      <div>
        {role !== 'system' && party_name && (
          <div className={`text-xs mb-1 ${role === 'party_a' || role === 'user' ? 'text-right' : ''} ${getLabelColor()}`}>
            {party_name}
          </div>
        )}
        <div className={getBubbleClass()}>{content}</div>
      </div>
    </div>
  )
}

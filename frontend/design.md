AI Document Intelligence Platform
DESIGN.md

Design Philosophy

Build a clean, premium SaaS application.

The design should feel similar to modern AI products like

ChatGPT
Claude
Notion AI
Linear
Vercel Dashboard

Avoid flashy gradients, excessive glassmorphism, or bright colors.

The interface should emphasize readability, simplicity, and professionalism.

Design Principles

Prioritize

clarity
consistency
accessibility
responsiveness
whitespace
hierarchy

Every component should look like it belongs to the same design system.

Color Palette
Background

Primary

#FFFFFF

Secondary

#F8FAFC

Sidebar

#F5F7FA
Text

Primary

#111827

Secondary

#6B7280

Muted

#9CA3AF
Primary Accent

Blue

#2563EB

Hover

#1D4ED8
Success
#10B981
Warning
#F59E0B
Error
#EF4444
Typography

Font

Inter

Fallback

sans-serif

Sizes

12
14
16
18
20
24
32

Weights

400
500
600
700
Border Radius

Cards

16px

Buttons

12px

Inputs

12px

Tags

999px
Shadows

Use only subtle shadows.

Never use heavy shadows.

0 2px 8px rgba(0,0,0,0.05)
Layout

Desktop

Sidebar

300px

Chat Area

Fluid

Maximum content width

900px
Sidebar

Contains

Logo
Upload button
Search documents
Document list
Status badges
Delete button

Each document card should display

PDF icon

Filename

Page count

Upload date

Status
Document Status

Processing

Yellow

Ready

Green

Failed

Red

Chat Layout

Top

Document title

Status

Actions

Middle

Conversation

Bottom

Chat input

Send button

Chat Messages

User

Right aligned

Blue bubble

Assistant

Left aligned

White card

Sources appear below every answer.

Source Cards

Each answer should show source cards.

Each source card contains

Page Number

Similarity Score

Snippet

Cards should be collapsible.

Upload Experience

Drag & Drop

OR

Upload Button

Show

Progress

Processing

Ready

Failure

Empty States

No documents

Illustration

Title

Description

Upload button

No chat

Friendly prompt

Buttons

Primary

Blue filled

Secondary

Gray outlined

Danger

Red

Inputs

Rounded

12px radius

Visible focus state

Placeholder text

Tables

Rounded

Alternating row hover

Minimal borders

Icons

Use

Lucide Icons

Only

No emojis.

Animations

Duration

200ms

Use

Fade

Slide

Scale

Avoid

Bounce

Rotate

Complex motion

Loading States

Skeleton loaders

Button spinner

Upload progress

Typing indicator

Responsive Behaviour

Desktop

Sidebar visible

Tablet

Collapsible sidebar

Mobile

Drawer navigation

Bottom-fixed chat input

No horizontal scrolling.

Accessibility

Minimum contrast ratio AA

Keyboard navigation

Visible focus

ARIA labels

Semantic HTML

Component Rules

Every UI component must be reusable.

Avoid duplicated HTML.

Avoid duplicated CSS.

Prefer utility classes.

CSS Organization
variables

layout

components

utilities

animations

responsive
JavaScript Organization
api.js

ui.js

app.js

helpers.js
Naming Convention

Classes

kebab-case

Variables

camelCase

Constants

UPPER_CASE
Future Compatibility

The design system must support future additions without redesign.

Examples

authentication
user profiles
multiple workspaces
dark mode
document folders
search
AI agents
analytics
admin dashboard

No existing component should need redesign when these features are added.

Definition of Done

The UI is complete only if it is

Responsive
Accessible
Consistent
Reusable
Modular
Performance optimized
Easy to extend
Portfolio quality
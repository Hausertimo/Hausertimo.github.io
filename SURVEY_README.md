# AI Survey Chat System

An interactive AI-powered survey system that uses LLMs to conduct conversational surveys with intelligent validation and sequential topic progression.

## 🎯 Features

- **20+ LLM Models**: Choose from OpenAI, Anthropic, Google, Mistral, Meta, and more
- **Customizable AI Personality**: Define character, tone, and behavior
- **Sequential Topic Validation**: AI validates responses before moving to next topic
- **Mandatory/Optional Topics**: Configure which questions require answers
- **Real-time Chat Interface**: Beautiful, responsive chat UI
- **Response Storage**: All conversations saved to Supabase
- **Admin Dashboard**: Create and manage surveys, view responses

## 📦 What's Included

### Files Created
- `/routes/survey.py` - Survey blueprint with all API endpoints
- `/templates/surveycreate.html` - Admin interface for creating surveys
- `/templates/survey.html` - Public chat interface for taking surveys
- `/survey_schema.sql` - Database schema for Supabase

### Routes Added
- `/surveycreate` - Admin page to create and manage surveys (requires auth)
- `/survey?id=<survey_id>` - Public survey chat interface
- `/api/surveys/*` - REST API for survey CRUD operations
- `/api/responses/*` - API for survey responses and chat

## 🚀 Setup Instructions

### 1. Create Database Tables

Run the SQL in `survey_schema.sql` in your Supabase SQL Editor:

```bash
# The file contains:
- surveys table (stores survey configurations)
- survey_responses table (stores conversations)
- Indexes for performance
- Row Level Security policies
```

### 2. Verify Environment Variables

Make sure these are set in your environment:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `openrouter` - OpenRouter API key (for LLM calls)
- `REDIS_URL` - Redis connection URL

### 3. Deploy

The system is already integrated into your Flask app. Just deploy and it's ready!

## 📖 How to Use

### Creating a Survey

1. Navigate to `/surveycreate` (requires login)
2. Fill in the survey details:
   - **Survey Name**: Give it a descriptive name
   - **AI Model**: Choose from 20+ available models
   - **Temperature**: Control creativity (0 = focused, 2 = creative)
   - **AI Character**: Define personality (e.g., "You are Emma, a friendly assistant...")
   - **Survey Brief**: Explain the survey purpose to the AI
   - **Topics**: Add topics you want to learn about (Name, Age, Job, etc.)
     - Set as mandatory or optional
     - Add descriptions for clarity
3. Click "Create Survey"
4. Copy the survey link to share

### Taking a Survey

1. Users visit `/survey?id=<survey_id>`
2. AI greets them and asks the first question
3. User responds naturally in chat
4. AI validates the response:
   - If satisfied → moves to next topic
   - If unclear → asks for clarification
5. Progress shown at top
6. Completion screen when done

### Viewing Responses

1. Go to `/surveycreate`
2. Find your survey in "Your Surveys"
3. Click "Responses" to view all conversations
4. Export data as needed

## 🎨 Design System

Follows NormScout design system:
- **Colors**: `#3869FA` (brand blue), `#2048D5` (headings), `#448CF7` (hover)
- **Spacing**: 16px (gaps), 24px (sections), 48px (major divisions)
- **Border Radius**: 12px (cards), 16px (modals)
- **Mobile-first responsive design**

## 🧠 How It Works

### Survey Creation Flow
1. Admin creates survey configuration
2. Selects LLM model and temperature
3. Defines AI character and behavior
4. Adds topics in desired order
5. Survey becomes active

### Survey Taking Flow
1. User starts survey → creates `survey_response` record
2. AI generates greeting and first question
3. For each user message:
   - AI validates response using LLM
   - Extracts clean value if satisfied
   - Moves to next topic or asks for clarification
4. Tracks progress through topics
5. Marks complete when all topics answered

### LLM Integration
- Uses OpenRouter API for flexibility
- Character prompt sets AI personality
- Survey brief provides context
- Topic descriptions guide questioning
- JSON validation for topic satisfaction

## 🔒 Security

- **Row Level Security**: Users only see their own surveys
- **Public Response Creation**: Anyone can take surveys
- **Auth Required**: Creating/managing surveys requires login
- **API Key Protection**: OpenRouter key stored in env vars

## 📊 Database Schema

### `surveys` table
- Survey configurations
- Model selection
- AI character/behavior
- Topics list (JSONB)

### `survey_responses` table
- Conversation history (JSONB)
- Current topic progress
- Completed topics (JSONB)
- Status tracking

## 🎯 Use Cases

- **Customer Feedback**: Interactive product surveys
- **Lead Qualification**: Conversational lead capture
- **Market Research**: Engaging data collection
- **User Onboarding**: Friendly information gathering
- **Event Registration**: Interactive RSVP forms
- **HR Interviews**: Pre-screening candidates

## 💡 Tips for Best Results

### AI Character Prompts
```
Good: "You are Emma, a friendly survey assistant. Be warm and brief."
Bad: "You are an AI that asks questions."
```

### Survey Briefs
```
Good: "This survey collects customer feedback about our SaaS product. Focus on usage patterns and satisfaction."
Bad: "Survey about stuff."
```

### Topic Descriptions
```
Good: name="Job Title", description="Current professional role or occupation"
Bad: name="Job", description="Job"
```

### Model Selection
- **Fast surveys**: Claude Haiku, GPT-4o Mini, Gemini Flash
- **Nuanced questions**: Claude Sonnet, GPT-4o, Mistral Large
- **Complex validation**: Claude Opus, GPT-5, Gemini Pro
- **Budget-friendly**: Any model with `:free` suffix

### Temperature Settings
- **0.0-0.3**: Consistent, focused responses (recommended for forms)
- **0.4-0.7**: Balanced creativity (recommended for feedback)
- **0.8-1.5**: Creative, varied responses (use cautiously)
- **1.6-2.0**: Very creative (not recommended for surveys)

## 🐛 Troubleshooting

**Survey not loading**
- Check survey ID in URL
- Verify survey is active (`is_active = true`)

**AI not validating responses**
- Check OpenRouter API key is set
- Verify model ID is correct
- Check OpenRouter account credits

**Responses not saving**
- Check Supabase connection
- Verify RLS policies are set correctly
- Check browser console for errors

## 🚀 Future Enhancements

Potential improvements:
- Analytics dashboard for responses
- Export responses to CSV/Excel
- Multi-language support
- Conditional topic branching
- Response analytics and insights
- Survey templates library
- A/B testing different AI personalities
- Integration with CRM systems

## 📝 API Reference

### Survey CRUD
- `POST /api/surveys/create` - Create new survey
- `GET /api/surveys` - List user's surveys
- `GET /api/surveys/<id>` - Get survey details
- `PUT /api/surveys/<id>` - Update survey
- `DELETE /api/surveys/<id>` - Deactivate survey

### Survey Responses
- `POST /api/surveys/<id>/start` - Start new response
- `POST /api/responses/<id>/message` - Submit user message
- `GET /api/surveys/<id>/responses` - Get all responses (auth required)

### Utilities
- `GET /api/models` - Get available LLM models

## 💰 Cost Considerations

- OpenRouter charges per token
- Free models available for testing
- Estimate: ~1000 tokens per survey completion
- Monitor usage in OpenRouter dashboard

## 🙌 Credits

Built for NormScout using:
- Flask (Python web framework)
- Supabase (Database & Auth)
- OpenRouter (LLM API)
- Redis (Caching)

---

**Ready to revolutionize surveys with AI?** 🚀

Head to `/surveycreate` and create your first interactive survey!

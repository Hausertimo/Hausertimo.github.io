# AI Survey Chat Builder - Complete Documentation

## Overview

A conversational AI-powered survey system integrated into your Flask/NormScout application. Surveys are conducted through natural chat conversations instead of traditional forms.

## Features

✅ **AI-Powered Conversations** - Uses OpenRouter LLM API (GPT-4, Claude, Llama, etc.)
✅ **Multiple Models** - Choose from 15+ AI models with different costs and capabilities
✅ **Custom Personas** - Define unique character personalities for each survey
✅ **Topic-Based Data Gathering** - Collect specific information in a natural flow
✅ **Mandatory & Optional Fields** - Configure which topics must be answered
✅ **Progress Tracking** - Visual progress bar shows completion percentage
✅ **Beautiful UI** - Professional SaaS design matching NormScout branding
✅ **Database Persistence** - All conversations and responses saved to Supabase
✅ **Analytics Dashboard** - View completion rates, response counts, and statistics

## Installation

### 1. Database Setup

Run the SQL migration in your Supabase SQL Editor:

```bash
# The schema file is located at:
database/survey_schema.sql
```

This creates:
- `survey_configs` - Survey configurations
- `survey_conversations` - Chat conversations and responses
- `survey_analytics` - Optional analytics tracking

### 2. Dependencies

All dependencies are already installed! The system uses:
- ✅ OpenRouter API (already configured)
- ✅ Supabase (already configured)
- ✅ Flask blueprints (already registered)

### 3. Environment Variables

Already configured:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_KEY` - Service key for database access
- `openrouter` - OpenRouter API key (yes, it's literally called "openrouter")

## Usage

### For Survey Creators (Admin)

#### 1. Access the Survey Builder

Navigate to: `https://yourdomain.com/surveycreate`

(Requires authentication)

#### 2. Create a New Survey

Click **"Create New Survey"** and configure:

**Survey Information:**
- Name (e.g., "Customer Feedback Survey")
- Description (optional)

**AI Configuration:**
- **Model**: Choose from 15+ models
  - **Recommended**: `openai/gpt-4o-mini` (fast, affordable, $0.0015/survey)
  - **Best Quality**: `anthropic/claude-3.5-sonnet` (best conversation, $0.033/survey)
  - **Free**: `meta-llama/llama-3.1-70b-instruct` (completely free!)

- **Temperature**: 0.0 (focused) to 1.0 (creative)
  - Recommended: 0.7 for natural conversations

- **Character Prompt**: Define the AI's personality
  ```
  Example:
  You are Emma, a friendly customer success manager.
  You're warm, professional, and genuinely interested in
  understanding the user's experience. Keep conversations
  natural and conversational.
  ```

- **Survey Purpose**: Explain to the AI why you're gathering data
  ```
  Example:
  We're gathering feedback to improve our product and
  better understand our customers' needs.
  ```

**Survey Topics:**
Add topics you want to gather (they're asked in order):

| Topic | Mandatory | Notes |
|-------|-----------|-------|
| Name | ✅ Yes | Basic identification |
| Email | ✅ Yes | Contact info |
| Company | ❌ No | Optional business context |
| Job Title | ❌ No | Optional role info |
| Product Usage | ✅ Yes | How they use your product |
| Pain Points | ✅ Yes | Problems they face |
| Feature Requests | ❌ No | What they want |

Click **"Create Survey"** to save!

#### 3. Get the Survey Link

After creating, click on the survey card → **"Copy Survey Link"**

The link format: `https://yourdomain.com/survey?id=<survey-id>`

Share this link with your audience!

#### 4. View Responses

- Click on any survey to see:
  - **Statistics**: Total conversations, completion rate, avg messages
  - **Recent Responses**: List of all submitted responses
  - **Gathered Data**: Full conversation transcripts

### For Survey Respondents (Public)

#### 1. Access Survey

Click the survey link you received.

#### 2. Complete the Conversation

- The AI introduces itself
- Answer questions naturally in the chat
- Progress bar shows completion
- Hit Enter or click Send

#### 3. View Summary

When complete, see a summary of your responses.

## API Endpoints

### Admin Routes (Auth Required)

```
POST   /api/survey/create                    # Create new survey
GET    /api/survey/configs                   # List all surveys
GET    /api/survey/config/<survey_id>        # Get survey details
PUT    /api/survey/config/<survey_id>        # Update survey
DELETE /api/survey/config/<survey_id>        # Delete survey (soft delete)

GET    /api/survey/responses/<survey_id>     # Get all responses
GET    /api/survey/conversation/<conv_id>    # Get conversation details
GET    /api/survey/stats/<survey_id>         # Get survey statistics
```

### Public Routes (No Auth)

```
GET    /survey?id=<survey_id>                # Survey chat page
POST   /api/survey/start                     # Start new conversation
POST   /api/survey/message                   # Send message, get AI response
```

## File Structure

```
├── database/
│   └── survey_schema.sql                    # Database schema
├── routes/
│   └── survey.py                            # Flask routes
├── services/
│   └── survey_chat.py                       # AI conversation logic
├── templates/
│   ├── survey_builder.html                  # Admin interface
│   ├── survey_chat.html                     # Public chat interface
│   └── error.html                           # Error page
├── static/js/
│   ├── survey_builder.js                    # Admin JS
│   └── survey_chat.js                       # Chat JS
└── app.py                                   # Blueprint registration
```

## How It Works

### Conversation Flow

```
1. User visits /survey?id=xyz
2. System loads survey config from database
3. AI generates welcome message using character prompt
4. AI asks first topic question
   ↓
5. User types response
6. AI analyzes if topic is complete
   ├─ Complete → Move to next topic
   └─ Incomplete → Ask follow-up question
7. Repeat until all topics covered
8. Show completion screen with gathered data
```

### AI Decision Making

For each user response, the AI:
1. **Analyzes Completion**: Is the answer sufficient?
2. **Extracts Data**: What information was provided?
3. **Decides Next Step**:
   - Complete → Next topic
   - Incomplete → Follow-up question
   - Optional declined → Skip to next

### Database Schema

**survey_configs**
```sql
- id (UUID)
- user_id (UUID, references auth.users)
- name (TEXT)
- model (TEXT, e.g., "openai/gpt-4o-mini")
- temperature (REAL)
- character_prompt (TEXT)
- survey_explanation (TEXT)
- topics (JSONB array)
- is_active (BOOLEAN)
```

**survey_conversations**
```sql
- id (UUID)
- survey_id (UUID, references survey_configs)
- messages (JSONB, full chat history)
- topic_progress (JSONB, completion tracking)
- status (TEXT: in_progress, completed, abandoned)
- gathered_data (JSONB, final structured data)
- completion_percentage (REAL)
```

## Model Recommendations

### Cost Comparison (per survey, ~3000 tokens)

| Model | Cost/Survey | Speed | Quality | Use Case |
|-------|-------------|-------|---------|----------|
| **GPT-4o Mini** | $0.0015 | ⚡⚡⚡ | ⭐⭐⭐⭐ | **Recommended** - Best balance |
| **Claude 3.5 Sonnet** | $0.033 | ⚡⚡ | ⭐⭐⭐⭐⭐ | Premium conversational quality |
| **Llama 3.1 70B** | FREE | ⚡⚡⚡ | ⭐⭐⭐ | Budget option (zero cost!) |
| **GPT-3.5 Turbo** | $0.001 | ⚡⚡⚡ | ⭐⭐⭐ | Cheapest paid option |
| **Gemini Flash** | $0.0008 | ⚡⚡⚡ | ⭐⭐⭐ | Fast and cheap |

### Temperature Guide

- **0.0-0.3**: Very focused, consistent (good for strict data collection)
- **0.5-0.7**: Balanced, natural (recommended for surveys)
- **0.8-1.0**: Creative, varied (good for engaging characters)

## Customization

### Styling

All styles use NormScout brand colors:
- Primary Blue: `#3869FA`
- Heading/CTA: `#2048D5`
- Hover: `#448CF7`
- Body Text: `#666666`

Edit templates to customize:
- `templates/survey_builder.html` - Admin interface
- `templates/survey_chat.html` - Public chat

### AI Behavior

Modify `services/survey_chat.py` functions:
- `analyze_topic_completion()` - How to determine if topic is complete
- `generate_survey_question()` - How questions are generated
- `generate_welcome_message()` - Welcome message format
- `generate_completion_message()` - Thank you message

## Troubleshooting

### "Survey not found"
- Check that survey is active (not deleted)
- Verify survey ID in URL is correct

### "Failed to start survey"
- Check OpenRouter API key is set
- Verify Supabase connection
- Check browser console for errors

### AI not responding
- Verify OpenRouter API has credits
- Check model name is correct (case-sensitive)
- Review network tab for API errors

### Responses not saving
- Verify Supabase RLS policies are set correctly
- Check user authentication (for admin routes)
- Review database logs

## Security Notes

- ✅ RLS policies protect user data
- ✅ Survey configs only visible to creators
- ✅ Public surveys accessible via URL (by design)
- ✅ Anonymous conversations supported
- ✅ Soft deletes prevent data loss

## Performance

### Optimizations
- Redis caching for OpenRouter responses (already configured)
- JSONB for flexible data storage
- Indexed columns for fast queries
- Minimal payload sizes

### Scaling
- Handles 1000s of concurrent conversations
- PostgreSQL (Supabase) scales automatically
- Stateless architecture (no sessions)

## Future Enhancements

Potential additions:
- [ ] Multi-language support
- [ ] Survey branching/conditional logic
- [ ] Email notifications on completion
- [ ] CSV export of responses
- [ ] Survey analytics dashboard
- [ ] A/B testing different character prompts
- [ ] Voice input/output
- [ ] Survey templates

## Support

For issues or questions:
1. Check this README
2. Review database logs in Supabase
3. Check OpenRouter usage dashboard
4. Review browser console for frontend errors

## License

Integrated into NormScout platform.

---

**Built with ❤️ for better survey experiences**

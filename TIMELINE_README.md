# Timeline Feature Documentation

## Overview

The Timeline Feature allows you to showcase your company's journey, milestones, and achievements in a beautiful, card-based timeline interface.

**Features:**
- Public timeline view at `/timeline` - Perfect for investors, customers, and team members
- Admin management panel at `/timelineadmin` - Easy content management
- Custom flairs/tags with colors for categorization (Funding, Product, Team, etc.)
- Expandable timeline entries with dates, topics, and detailed descriptions
- Fully responsive design matching NormScout's design system
- Secure authentication for admin operations

## Files Structure

```
routes/
  └── timeline.py              # Flask blueprint with all routes and API endpoints

templates/
  ├── timeline.html            # Public timeline view
  └── timeline_admin.html      # Admin management interface
```

All timeline code is isolated in these files for easy integration into your full product!

## Database Setup

### Step 1: Run SQL in Supabase SQL Editor

Execute the following SQL to create the necessary tables and policies:

```sql
-- Timeline Flairs (tags with colors)
CREATE TABLE IF NOT EXISTS public.timeline_flairs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL DEFAULT '#3869FA',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Timeline Entries
CREATE TABLE IF NOT EXISTS public.timeline_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    topic TEXT NOT NULL,
    description TEXT,
    flair_id UUID REFERENCES public.timeline_flairs(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_timeline_entries_date ON public.timeline_entries(date DESC);

-- RLS Policies (Public read, authenticated write)
ALTER TABLE public.timeline_flairs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.timeline_entries ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Allow public read access to flairs"
    ON public.timeline_flairs FOR SELECT USING (true);

CREATE POLICY "Allow public read access to entries"
    ON public.timeline_entries FOR SELECT USING (true);

-- Allow authenticated users to manage
CREATE POLICY "Allow authenticated users to manage flairs"
    ON public.timeline_flairs FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to manage entries"
    ON public.timeline_entries FOR ALL USING (auth.role() = 'authenticated');
```

## Integration

The timeline blueprint is already integrated into `app.py`:

```python
from routes.timeline import timeline_bp, init_dependencies as init_timeline_deps

# Register blueprint
app.register_blueprint(timeline_bp)

# Initialize dependencies
init_timeline_deps(supabase)
```

## Usage

### For Admins: Managing Timeline

1. **Login** to your account (admin panel requires authentication)

2. **Navigate** to `/timelineadmin`

3. **Create Flairs** (Categories):
   - Click "New Flair"
   - Enter name (e.g., "Funding", "Product", "Team")
   - Choose a color (8 preset colors available or custom hex)
   - Save

4. **Create Timeline Entries**:
   - Click "New Entry"
   - Select date of the milestone
   - Enter topic/title (e.g., "Secured Series A Funding")
   - Choose a flair/category (optional)
   - Add detailed description (optional)
   - Save

5. **Edit/Delete** entries and flairs as needed

### For Public: Viewing Timeline

- Navigate to `/timeline`
- View all milestones in chronological order (newest first)
- Click "Read more" to expand long descriptions
- See color-coded flairs for each milestone
- No authentication required

## API Endpoints

### Timeline Entries

- `GET /api/timeline/entries` - Get all timeline entries (public)
- `POST /api/timeline/entries` - Create new entry (authenticated)
- `PUT /api/timeline/entries/<id>` - Update entry (authenticated)
- `DELETE /api/timeline/entries/<id>` - Delete entry (authenticated)

### Flairs/Tags

- `GET /api/timeline/flairs` - Get all flairs (public)
- `POST /api/timeline/flairs` - Create new flair (authenticated)
- `PUT /api/timeline/flairs/<id>` - Update flair (authenticated)
- `DELETE /api/timeline/flairs/<id>` - Delete flair (authenticated)

## Example Timeline Entry Data

```json
{
  "date": "2024-03-15",
  "topic": "Accepted to Kick Venture Accelerator",
  "description": "We're thrilled to announce that we've been accepted into the prestigious Kick Venture accelerator program. This marks a major milestone in our journey to revolutionize compliance technology.",
  "flair_id": "uuid-of-funding-flair"
}
```

## Example Flair Data

```json
{
  "name": "Funding",
  "color": "#10B981"
}
```

## Design System

The timeline uses NormScout's design system:

**Colors:**
- Brand Blue: `#3869FA` (accents, borders)
- Royal Blue: `#2048D5` (headings, CTAs)
- Accent Blue: `#448CF7` (hover states)
- Text Dark: `#1a1a1a` (primary text)
- Text Light: `#666666` (body text)

**Spacing:**
- Default gaps: 16px
- Between sections: 24px
- Major divisions: 48px

**Components:**
- Cards: 12px border-radius, box-shadow on hover
- Buttons: `btn btn-accent` (primary), `btn btn-primary` (secondary), `btn btn-danger` (delete)
- Hover effect: `translateY(-2px)` + shadow

## Customization

### Change Timeline Title

Edit `templates/timeline.html`:

```html
<h1 class="timeline-main-title">Our Journey</h1>
<p class="timeline-subtitle">Tracking our progress and achievements</p>
```

### Restrict Admin Access

By default, any authenticated user can manage the timeline. To restrict to specific users:

1. Update the Supabase RLS policies to check for specific user IDs or roles
2. Or add custom middleware in `routes/timeline.py`

Example policy for specific users:

```sql
CREATE POLICY "Allow specific users to manage flairs"
    ON public.timeline_flairs FOR ALL
    USING (auth.uid() IN (
        'user-uuid-1',
        'user-uuid-2'
    ));
```

## Troubleshooting

**Issue**: Timeline entries not showing
- Check Supabase connection
- Verify database tables were created
- Check RLS policies allow public read access

**Issue**: Can't create/edit entries
- Verify user is authenticated
- Check RLS policies allow authenticated writes
- Verify Supabase client is initialized

**Issue**: Flairs not appearing in dropdown
- Create at least one flair first
- Check browser console for API errors

## Example Use Cases

1. **Startup Journey**: Show funding rounds, product launches, team milestones
2. **Product Roadmap**: Display feature releases and updates
3. **Company History**: Chronicle important company events
4. **Project Timeline**: Track project phases and deliverables
5. **Investor Updates**: Showcase achievements and progress

## Benefits

✅ **Easy to Integrate**: All code isolated in separate files
✅ **Fully Responsive**: Works on mobile, tablet, and desktop
✅ **Secure**: Authentication required for admin operations
✅ **Customizable**: Flairs with custom colors for branding
✅ **Professional Design**: Matches NormScout's SaaS aesthetic
✅ **SEO Friendly**: Public timeline is crawlable

## Support

For questions or issues, refer to:
- Flask documentation: https://flask.palletsprojects.com/
- Supabase documentation: https://supabase.com/docs
- NormScout design system: `/static/style.css`

---

**Ready to showcase your journey!** 🚀

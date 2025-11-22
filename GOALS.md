# Project Goals & Objectives

## Vision

Build a **social-first recommendation engine** that helps users discover venues based on a combination of their personal preferences and their social circle's activity, creating a more engaging and trustworthy discovery experience.

## Core Problem

Traditional recommendation systems focus solely on individual user preferences, missing the crucial social dimension:
- **"My friends are going to this bar tonight"** is more compelling than **"This bar matches your taste profile"**
- Social proof drives real-world decisions
- Friend activity creates FOMO (Fear of Missing Out) and increases engagement

## Solution

A hybrid recommendation system that:
1. **Understands user preferences** via vector embeddings (semantic similarity)
2. **Tracks social connections** via a graph database
3. **Combines both signals** to rank venues by relevance AND social proof
4. **Provides transparency** by explaining why each recommendation appears

## Primary Use Cases

### 1. Social Discovery
**User Story**: *"I want to see where my friends are going this weekend"*

- User opens their feed
- Sees venues ranked by friend activity
- Each venue shows which friends are going/interested
- Can immediately book or save for later

### 2. Taste-Based Discovery
**User Story**: *"I love jazz clubs, show me new ones"*

- System learns user interests (e.g., "Jazz", "Cocktails")
- Vector search finds semantically similar venues
- Social layer boosts venues friends have visited
- User discovers new places aligned with their taste

### 3. Group Planning
**User Story**: *"Find a restaurant my friend group would all enjoy"*

- System analyzes mutual friends' preferences
- Identifies venues with high overlap
- Shows social proof ("5 mutual friends liked this")
- Facilitates consensus decision-making

## Success Metrics

### Engagement
- **Click-through rate** on recommended venues
- **Conversion rate** from view → save → going
- **Time spent** exploring recommendations

### Social Proof Impact
- **Lift in engagement** for venues with friend activity vs. without
- **Viral coefficient** (how many friends a user influences)

### Accuracy
- **Precision@K** for top-K recommendations
- **User satisfaction** ratings
- **Repeat visit rate** for recommended venues

## Technical Goals

### MVP (Current Phase)
- [x] Functional recommendation engine combining vector + graph
- [x] Interactive UI for simulation and testing
- [x] Async processing for scalability
- [x] Agentic booking workflow (LangGraph)

### Future Enhancements
- [ ] Real-time updates (WebSockets for live friend activity)
- [ ] Mobile app (React Native)
- [ ] Advanced personalization (collaborative filtering)
- [ ] Event-based recommendations (concerts, pop-ups)
- [ ] Group chat integration (WhatsApp, Telegram)

## Non-Goals (Out of Scope for MVP)

- **User authentication** - Using simulated users for testing
- **Payment processing** - Booking agent is conceptual
- **Real venue data** - Using synthetic data for demonstration
- **Production deployment** - Local development only
- **Advanced ML models** - Using mock embeddings, not trained models

## Target Audience

### Primary
- **Product Managers** evaluating social recommendation approaches
- **Engineers** learning graph + vector hybrid systems
- **Investors** assessing feasibility of social discovery platforms

### Secondary
- **Researchers** studying social influence in recommendations
- **Designers** prototyping social discovery UX

## Competitive Differentiation

Unlike existing platforms:
- **Yelp/Google Maps**: No social graph, purely algorithmic
- **Instagram/Facebook**: Social-first but not location-optimized
- **Foursquare**: Had social features but deprecated them

**Our Approach**: Combines the best of both - algorithmic precision with social context.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cold start (new users with no friends) | Low engagement | Fallback to pure vector search |
| Privacy concerns (exposing friend activity) | User trust | Opt-in sharing, granular controls |
| Filter bubble (only seeing friend preferences) | Limited discovery | Inject diverse recommendations |
| Scalability (graph queries expensive) | Performance | Caching, denormalization, read replicas |

## Roadmap

### Phase 1: Foundation ✅
- Core recommendation algorithm
- Basic UI for testing
- Data seeding

### Phase 2: Polish ✅
- Modern UI redesign
- Bug fixes
- Documentation

### Phase 3: Intelligence (Future)
- Real embeddings (OpenAI, Cohere)
- Collaborative filtering
- A/B testing framework

### Phase 4: Scale (Future)
- Production infrastructure
- Real-time features
- Mobile apps

## Conclusion

This MVP demonstrates the **technical feasibility** and **product potential** of a social-first recommendation engine. The next steps involve user testing, refining the ranking algorithm, and building production-ready infrastructure.

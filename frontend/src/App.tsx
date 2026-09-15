import { useEffect, useState } from 'react'
import './App.css'

type Application = {
  slug: string
  name: string
  organisation: string
  summary: string
  year?: number
  country: string
  category: string
  status: 'Verified' | 'Review'
  website?: string
  description: string
  technologies: string[]
}

const applications: Application[] = [
  {
    slug: 'tractrac-plus',
    name: 'TracTrac Plus',
    organisation: 'TracTrac Mechanization Services Limited',
    summary: 'A practical coordination layer for agricultural machinery and field services.',
    year: 2022,
    country: 'Nigeria',
    category: 'Crop production tools',
    status: 'Verified',
    website: 'https://example.com',
    description: 'TracTrac Plus helps farmers discover and coordinate mechanisation services across growing regions.',
    technologies: ['GIS remote sensing', 'Mobile app'],
  },
  {
    slug: 'field-notes',
    name: 'Field Notes',
    organisation: 'Harvest Systems',
    summary: 'Simple digital records for teams working across distributed farms.',
    country: 'Kenya',
    category: 'Farm management',
    status: 'Review',
    description: 'Field Notes keeps observations, tasks, and seasonal decisions together for agricultural teams.',
    technologies: ['Mobile app', 'Data platform'],
  },
  {
    slug: 'agri-metrique',
    name: 'Agri Metrique',
    organisation: 'Terra Commons',
    summary: 'An open toolkit for turning local crop observations into useful signals.',
    year: 2024,
    country: 'Rwanda',
    category: 'Data and analytics',
    status: 'Verified',
    description: 'Agri Metrique brings community observations and lightweight analytics into one approachable workspace.',
    technologies: ['Data platform', 'Analytics'],
  },
]

const categories = ['All categories', ...new Set(applications.map((application) => application.category))]
const countries = ['All countries', ...new Set(applications.map((application) => application.country))]

function navigate(path: string) {
  window.history.pushState({}, '', path)
  window.dispatchEvent(new PopStateEvent('popstate'))
}

function App() {
  const [path, setPath] = useState(window.location.pathname)

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname)
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  const selected = applications.find((application) => application.slug === path.split('/')[2])

  return (
    <div className="app-shell">
      <header className="site-header">
        <button className="brand" onClick={() => navigate('/applications')}>
          <span className="brand-mark">AE</span>
          <span>Agritech Ecosystem</span>
        </button>
        <nav aria-label="Primary navigation">
          <button className="nav-link active" onClick={() => navigate('/applications')}>Applications</button>
          <span className="nav-link muted">Insights <span className="soon">Soon</span></span>
        </nav>
        <span className="edition">Pilot directory / 2024</span>
      </header>
      {path.startsWith('/applications/') ? <Profile application={selected} /> : <Directory />}
    </div>
  )
}

function Directory() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState(categories[0])
  const [country, setCountry] = useState(countries[0])
  const filtered = applications.filter((application) => {
    const haystack = `${application.name} ${application.organisation} ${application.summary}`.toLowerCase()
    return haystack.includes(search.toLowerCase()) &&
      (category === categories[0] || application.category === category) &&
      (country === countries[0] || application.country === country)
  })

  return (
    <main>
      <section className="directory-intro">
        <div className="eyebrow">Field guide / 01</div>
        <h1>Find the tools<br /><em>moving agriculture forward.</em></h1>
        <p className="intro-copy">A considered directory of digital products, platforms, and practical systems shaping food and farming.</p>
        <div className="intro-rule" />
        <div className="intro-meta"><span>03 featured records</span><span>Updated 14 Sep 2024</span></div>
      </section>
      <section className="catalogue" aria-label="Application directory">
        <div className="catalogue-toolbar">
          <label className="search-field"><span>⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search applications or organisations" /></label>
          <label><span className="filter-label">Category</span><select value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label><span className="filter-label">Country</span><select value={country} onChange={(event) => setCountry(event.target.value)}>{countries.map((item) => <option key={item}>{item}</option>)}</select></label>
        </div>
        <div className="results-header"><span><strong>{filtered.length.toString().padStart(2, '0')}</strong> applications in view</span><span className="view-note">Showing featured pilot records</span></div>
        {filtered.length ? <div className="application-grid">{filtered.map((application, index) => <ApplicationCard key={application.slug} application={application} index={index} />)}</div> : <div className="empty-state"><strong>No applications found.</strong><span>Try broadening your search or clearing a filter.</span></div>}
      </section>
    </main>
  )
}

function ApplicationCard({ application, index }: { application: Application; index: number }) {
  return (
    <article className="application-card" style={{ '--delay': `${index * 90}ms` } as React.CSSProperties}>
      <div className="card-topline"><span>0{index + 1}</span><span className={application.status === 'Verified' ? 'status verified' : 'status'}>{application.status}</span></div>
      <div className="card-body"><p className="card-category">{application.category}</p><h2>{application.name}</h2><p className="card-summary">{application.summary}</p></div>
      <div className="card-footer"><span>{application.organisation}</span><button onClick={() => navigate(`/applications/${application.slug}`)} aria-label={`View ${application.name}`}>View profile <span>↗</span></button></div>
    </article>
  )
}

function Profile({ application }: { application?: Application }) {
  if (!application) return <main className="not-found"><span className="eyebrow">404 / Not found</span><h1>This record has<br /><em>not been found.</em></h1><button className="back-button" onClick={() => navigate('/applications')}>← Back to directory</button></main>
  return <main className="profile"><button className="back-link" onClick={() => navigate('/applications')}>← All applications</button><div className="profile-heading"><p className="eyebrow">Application profile / {application.country}</p><h1>{application.name}</h1><p className="profile-lede">{application.summary}</p></div><div className="profile-layout"><aside><span className="aside-label">At a glance</span><dl><div><dt>Organisation</dt><dd>{application.organisation}</dd></div><div><dt>Category</dt><dd>{application.category}</dd></div><div><dt>Launch year</dt><dd>{application.year ?? 'Not recorded'}</dd></div><div><dt>Location</dt><dd>{application.country}</dd></div></dl>{application.website && <a className="website-link" href={application.website} target="_blank" rel="noreferrer">Visit website ↗</a>}</aside><section className="profile-content"><p>{application.description}</p><h2>What it connects</h2><div className="tag-list">{application.technologies.map((technology) => <span key={technology}>{technology}</span>)}</div></section></div></main>
}

export default App

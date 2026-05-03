import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div className="home">
      <div className="home-logo">🛡️</div>
      <h1>PathShield AI</h1>
      <p className="tagline">Protecting every journey with AI</p>
      <div className="home-actions">
        <Link to="/submit" className="btn btn-primary">
          🚨 Submit Road Report
        </Link>
        <Link to="/sos" className="btn btn-danger">
          🆘 Emergency SOS
        </Link>
        <Link to="/public-dashboard" className="btn btn-outline">
          🌐 Public Dashboard
        </Link>
      </div>
    </div>
  );
}

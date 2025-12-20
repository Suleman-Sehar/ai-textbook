import React from 'react';
import Layout from '@theme/Layout';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Link from '@docusaurus/Link';

function NotFound() {
  const { siteConfig } = useDocusaurusContext();

  return (
    <Layout title="Page Not Found" description="The page you are looking for does not exist">
      <main className="container margin-vert--xl">
        <div className="row">
          <div className="col col--6 col--offset-3">
            <h1>Page Not Found</h1>
            <p>We couldn't find the page you were looking for.</p>
            <p>Please check the URL or use the navigation to find what you're looking for.</p>
            <div style={{ marginTop: '2rem' }}>
              <Link to="/" className="button button--primary button--lg">
                Go Home
              </Link>
              <Link
                to="/docs/intro"
                className="button button--secondary button--lg"
                style={{ marginLeft: '1rem' }}
              >
                Textbook Home
              </Link>
            </div>
          </div>
        </div>
      </main>
    </Layout>
  );
}

export default NotFound;
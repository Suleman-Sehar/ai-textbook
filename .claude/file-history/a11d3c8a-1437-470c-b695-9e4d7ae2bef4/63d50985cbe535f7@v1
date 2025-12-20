import React from 'react';
import Layout from '@theme/Layout';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';

function ErrorPage() {
  const { siteConfig } = useDocusaurusContext();

  return (
    <Layout title="Error" description="An error occurred in the application">
      <main className="container margin-vert--xl">
        <div className="row">
          <div className="col col--6 col--offset-3">
            <h1>Error</h1>
            <p>Oops! Something went wrong on our end.</p>
            <p>We've been notified of this issue and are working to fix it.</p>
            <div style={{ marginTop: '2rem' }}>
              <a href="/" className="button button--primary button--lg">
                Go Home
              </a>
              <a
                href={siteConfig.customFields?.supportUrl || 'https://github.com/ai-textbook/physical-ai-textbook/issues'}
                className="button button--secondary button--lg"
                style={{ marginLeft: '1rem' }}
              >
                Report Issue
              </a>
            </div>
          </div>
        </div>
      </main>
    </Layout>
  );
}

export default ErrorPage;
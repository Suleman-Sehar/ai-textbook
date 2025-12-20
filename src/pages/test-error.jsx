import React, { Component } from 'react';

// A component that will throw an error to test error boundaries
class ErrorTestComponent extends Component {
  constructor(props) {
    super(props);
    this.state = { throwError: false };
  }

  render() {
    if (this.state.throwError) {
      throw new Error('Test error for error boundary verification');
    }

    return (
      <div>
        <h1>Error Handling Test Page</h1>
        <p>This page tests the error handling functionality of the AI textbook.</p>
        <button
          onClick={() => this.setState({ throwError: true })}
          style={{
            padding: '10px 20px',
            backgroundColor: '#ff6b6b',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Trigger Test Error
        </button>
        <p>Click the button above to trigger an error and test the error boundary.</p>
      </div>
    );
  }
}

export default function ErrorTestPage() {
  return (
    <div>
      <ErrorTestComponent />
    </div>
  );
}
import { useState } from "react";

type BenefitCardProps = {
  schemeName: string;
  category: string;
  description: string;
  eligibilityStatus: string;
};

function BenefitCard({
  schemeName,
  category,
  description,
  eligibilityStatus,
}: BenefitCardProps) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div>
      <p>{category}</p>

      <h2>{schemeName}</h2>

      <p>{description}</p>

      <strong>{eligibilityStatus}</strong>

      <br />

      <button onClick={() => setShowDetails(!showDetails)}>
        {showDetails ? "Hide Details" : "View Benefit"}
      </button>

      {showDetails && (
        <div>
          <ul>
            <h2>Required Documents</h2>
            <li>Aadhaar</li>
            <li>Bank Account Details</li>
          </ul>
          <p>
            This benefit may be relevant based on the information available
            in your profile.
          </p>
        </div>
      )}
    </div>
  );
}

export default BenefitCard;
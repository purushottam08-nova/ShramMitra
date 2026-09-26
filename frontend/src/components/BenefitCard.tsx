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
  return (
    <div>
      <p>{category}</p>

      <h2>{schemeName}</h2>

      <p>{description}</p>

      <strong>{eligibilityStatus}</strong>

      <br />

      <button>View Benefit</button>
    </div>
  );
}

export default BenefitCard;
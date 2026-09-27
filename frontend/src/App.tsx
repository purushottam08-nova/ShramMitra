import BenefitCard from "./components/BenefitCard";

const benefits = [
  {
    id: 1,
    schemeName: "PM-SYM",
    category: "Pension",
    description: "Pension support for eligible unorganised workers.",
    eligibilityStatus: "Potentially Eligible",
  },
  {
    id: 2,
    schemeName: "Worker Accident Assistance",
    category: "Accident Support",
    description:
      "Financial assistance subject to applicable eligibility conditions.",
    eligibilityStatus: "Missing Information",
  },
  {
    id: 3,
    schemeName: "Health Support",
    category: "Healthcare",
    description: "Health-related support for eligible workers.",
    eligibilityStatus: "Additional Verification Required",
  },
];

function App() {
  return (
    <main>
      <h1>ShramMitra</h1>
      <p>Benefits, applications and support — in one place.</p>

      {benefits.map((benefit) => (
        <BenefitCard
          key={benefit.id}
          schemeName={benefit.schemeName}
          category={benefit.category}
          description={benefit.description}
          eligibilityStatus={benefit.eligibilityStatus}
        />
      ))}
    </main>
  );
}

export default App;
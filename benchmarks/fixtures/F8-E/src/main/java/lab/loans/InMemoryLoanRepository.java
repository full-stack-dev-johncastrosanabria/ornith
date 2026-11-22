package lab.loans;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public final class InMemoryLoanRepository implements LoanRepository {
    private final Map<String, Loan> loans = new LinkedHashMap<>();

    @Override
    public void save(Loan loan) {
        loans.put(loan.getId(), loan);
    }

    @Override
    public Optional<Loan> find(String loanId) {
        return Optional.ofNullable(loans.get(loanId));
    }

    @Override
    public List<Loan> openLoansOf(String memberId) {
        return loans.values().stream().filter(l -> l.isOpen() && l.getMemberId().equals(memberId)).toList();
    }

    @Override
    public Optional<Loan> openLoanFor(String isbn) {
        return loans.values().stream().filter(l -> l.isOpen() && l.getIsbn().equals(isbn)).findFirst();
    }
}

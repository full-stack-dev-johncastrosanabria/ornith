package lab.loans;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;

/** Lending operations of the branch library. Dates are passed in explicitly. */
public class LoanService {
    private final LoanRepository loans;
    private final LoanPolicy policy;
    private final Map<String, Member> members = new HashMap<>();
    private int sequence;

    public LoanService(LoanRepository loans, LoanPolicy policy) {
        this.loans = loans;
        this.policy = policy;
    }

    public void register(Member member) {
        members.put(member.id(), member);
    }

    /** Lends a book. A member holds at most {@link MemberType#maxLoans()} open loans; a book is on at most one open loan. */
    public Loan borrow(String memberId, String isbn, LocalDate today) {
        Member member = member(memberId);
        if (loans.openLoansOf(memberId).size() >= member.type().maxLoans()) {
            throw new LoanException("loan limit reached for " + memberId);
        }
        if (loans.openLoanFor(isbn).isPresent()) {
            throw new LoanException("book already on loan: " + isbn);
        }
        Loan loan = new Loan("L" + (++sequence), memberId, isbn, today, policy.dueDate(today, member.type()));
        loans.save(loan);
        return loan;
    }

    /** Ends an open loan and returns the late fee owed (zero when on time). */
    public BigDecimal giveBack(String loanId, LocalDate today) {
        Loan loan = open(loanId);
        loan.markReturned(today);
        loans.save(loan);
        return policy.lateFee(loan.getDueOn(), today);
    }

    /**
     * Renews an open loan once. The new due date is the current due date plus the member type's loan days,
     * moved to the following Monday when it falls on a weekend. Renewing on the due date itself is allowed.
     *
     * @throws LoanException when the loan does not exist, was returned, is overdue on {@code today},
     *                       or has already been renewed
     */
    public Loan renew(String loanId, LocalDate today) {
        Loan loan = open(loanId);
        if (today.isAfter(loan.getDueOn())) {
            throw new LoanException("loan is overdue: " + loanId);
        }
        if (loan.getRenewals() > 0) {
            throw new LoanException("loan already renewed: " + loanId);
        }
        MemberType type = member(loan.getMemberId()).type();
        loan.renew(policy.nextBusinessDay(loan.getDueOn().plusDays(type.loanDays())));
        loans.save(loan);
        return loan;
    }

    private Member member(String memberId) {
        Member member = members.get(memberId);
        if (member == null) {
            throw new LoanException("unknown member " + memberId);
        }
        return member;
    }

    private Loan open(String loanId) {
        Loan loan = loans.find(loanId).orElseThrow(() -> new LoanException("unknown loan " + loanId));
        if (!loan.isOpen()) {
            throw new LoanException("loan already returned: " + loanId);
        }
        return loan;
    }
}

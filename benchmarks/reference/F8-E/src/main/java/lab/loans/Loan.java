package lab.loans;

import java.time.LocalDate;

public final class Loan {
    private final String id;
    private final String memberId;
    private final String isbn;
    private final LocalDate borrowedOn;
    private LocalDate dueOn;
    private LocalDate returnedOn;
    private int renewals;

    Loan(String id, String memberId, String isbn, LocalDate borrowedOn, LocalDate dueOn) {
        this.id = id;
        this.memberId = memberId;
        this.isbn = isbn;
        this.borrowedOn = borrowedOn;
        this.dueOn = dueOn;
    }

    public String getId() {
        return id;
    }

    public String getMemberId() {
        return memberId;
    }

    public String getIsbn() {
        return isbn;
    }

    public LocalDate getBorrowedOn() {
        return borrowedOn;
    }

    public LocalDate getDueOn() {
        return dueOn;
    }

    public LocalDate getReturnedOn() {
        return returnedOn;
    }

    public int getRenewals() {
        return renewals;
    }

    public boolean isOpen() {
        return returnedOn == null;
    }

    void renew(LocalDate newDueOn) {
        this.dueOn = newDueOn;
        this.renewals++;
    }

    void markReturned(LocalDate day) {
        this.returnedOn = day;
    }
}
